/* Live native Odoo browser evidence; credentials, identities and failures stay in .local. */
const {chromium}=require('../frontend/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),local=path.join(root,'.local/ui-shell-auth001');
const target=process.argv[2]||'clone';assert(['clone','dev'].includes(target));
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const owner=read('.local/ui-shell-auth001/owner.json');assert(owner.rehearsal_passed&&owner.http_port===19189);
const base=`http://127.0.0.1:${target==='dev'?18069:19189}`;
const actors=read('.local/kd-access001/dev-credentials.json');actors.admin={login:'admin',password:read('.local/dev-secrets.json').admin};
const out=path.join(local,'shots',target);fs.mkdirSync(out,{recursive:true});
const checks=[],errors=[],failures=[];let current;
const redact=s=>Object.values(actors).reduce((v,a)=>v.replaceAll(a.password,'[REDACTED]'),String(s));
const check=(name,value)=>{assert(value,name);checks.push(name)};
function hashes(){const result={};for(const m of ['tp_web_home','tp_web_login']){const dir=path.join(root,target==='clone'?'.local/ui-shell-auth001/source/custom_addons':'custom_addons',m);const h={};const walk=d=>{for(const e of fs.readdirSync(d,{withFileTypes:true})){if(e.name==='__pycache__'||e.name.endsWith('.pyc'))continue;const f=path.join(d,e.name);if(e.isDirectory())walk(f);else h[path.relative(dir,f).split(path.sep).join('/')]=crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex')}};walk(dir);result[m]=h}return result}
const initial=hashes();
async function shot(p,name){await p.screenshot({path:path.join(out,name+'.png'),animations:'disabled'});}
async function overflow(p,name){check(name+' no horizontal overflow',await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));}
async function rpc(c,model,method,args=[],kwargs={}){const data=await(await c.request.post(base+`/web/dataset/call_kw/${model}/${method}`,{data:{jsonrpc:'2.0',method:'call',params:{model,method,args,kwargs}}})).json();assert(!data.error,'RPC failed');return data.result}
async function info(c){return(await(await c.request.post(base+'/web/session/get_session_info',{data:{jsonrpc:'2.0',method:'call',params:{}}})).json()).result}
async function login(p,a,redirect=''){await p.goto(base+'/web/login'+(redirect?'?redirect='+encodeURIComponent(redirect):''));if(await p.locator('.tp-account-other').isVisible())await p.locator('.tp-account-other').click();await p.locator('form [name=login]').fill(a.login);await p.locator('form [name=password]').fill(a.password);await p.locator('form [name=password]').press('Enter');await p.locator('.tp-shell-navbar').waitFor({timeout:120000});}
async function logout(p){await p.setViewportSize({width:1440,height:900});await p.locator('.o_user_menu').click();const response=p.waitForResponse(r=>r.url().includes('/web/session/logout')&&r.request().method()==='POST');await p.locator('[data-menu=logout]').click();await response;await p.locator('.tp-native-login').waitFor({timeout:60000});}
async function context(b){const c=await b.newContext({viewport:{width:1440,height:900},locale:'vi-VN'});const p=await c.newPage();current=p;p.on('pageerror',e=>errors.push(redact(e.message)));p.on('console',m=>{if(m.type()==='error')errors.push(redact(m.text()))});return[c,p];}
async function authScreens(b){const[c,p]=await context(b);try{
 await p.goto(base+'/web/login');await p.locator('form [name=login]').waitFor({state:'visible'});
 check('0 remembered users displays password form',!await p.locator('.o_user_switch').count());
 for(const[w,h]of [[1440,900],[1280,800],[768,1024],[390,844],[320,844]]){await p.setViewportSize({width:w,height:h});await overflow(p,'login '+w);await shot(p,'login-'+w);check('login layout '+w,await p.locator('.tp-native-login').evaluate((e,w)=>getComputedStyle(e).display===(w<768?'flex':'grid'),w));}
 await p.setViewportSize({width:1440,height:900});
 await p.locator('[name=login]').fill('invalid.synthetic');await p.locator('[name=password]').fill('wrong-password');
 await p.getByRole('button',{name:'Hiện mật khẩu',exact:true}).click();check('show password and ARIA',await p.locator('[name=password]').getAttribute('type')==='text'&&await p.locator('.o_show_password').getAttribute('aria-pressed')==='true');
 await p.getByRole('button',{name:'Ẩn mật khẩu',exact:true}).click();check('hide password',await p.locator('[name=password]').getAttribute('type')==='password');
 if(target==='clone'){
  await p.locator('[name=password]').press('Enter');await p.locator('.alert-danger').waitFor();check('wrong login generic Vietnamese',/Tên đăng nhập hoặc mật khẩu/.test(await p.locator('.alert-danger').innerText()));check('server error allows retry',await p.locator('button[type=submit]').first().isEnabled());await shot(p,'login-error');
 }
 const remembered=[{login:'synthetic.one',name:'Tài khoản kiểm thử tên dài '.repeat(4),partnerId:0,userId:9001,partnerWriteDate:''},{login:'synthetic.two',name:'Tài khoản kiểm thử',partnerId:0,userId:9002,partnerWriteDate:''}];
 await p.evaluate(u=>localStorage.setItem('web.lastConnectedUser',JSON.stringify(u)),remembered);await p.goto(base+'/web/login');await p.locator('.tp-account-row').first().waitFor();
 check('2 remembered accounts',await p.locator('.tp-account-row').count()===2);check('no nested buttons',await p.locator('button button').count()===0);
 for(const w of[1440,390,320]){await p.setViewportSize({width:w,height:w===1440?900:844});await overflow(p,'chooser '+w);await shot(p,'chooser-'+w)}
 check('avatar fallback exists',await p.locator('.tp-account-avatar > span').first().innerText()==='T');
 await p.locator('.tp-account-select').first().focus();await p.keyboard.press('Enter');check('selection fills only login',await p.locator('[name=login]').inputValue()==='synthetic.one'&&await p.locator('[name=password]').inputValue()==='');check('selection is not authentication',!(await info(c))?.uid);
 await p.getByRole('button',{name:'Chọn tài khoản',exact:true}).click();await p.getByRole('button',{name:'Bỏ khỏi thiết bị này',exact:true}).first().focus();await p.keyboard.press('Enter');check('remove one uses native storage',await p.evaluate(()=>JSON.parse(localStorage.getItem('web.lastConnectedUser')).length)===1);
 await p.locator('.tp-account-row').nth(1).waitFor({state:'hidden'});await p.getByRole('button',{name:'Bỏ khỏi thiết bị này',exact:true}).click();await p.locator('[name=login]').waitFor({state:'visible'});await p.locator('.tp-account-row').waitFor({state:'hidden'});check('remove all returns form',await p.locator('.tp-account-row').count()===0);
 await p.evaluate(u=>localStorage.setItem('web.lastConnectedUser',JSON.stringify([u])),remembered[0]);await p.reload();await p.locator('[name=login]').waitFor({state:'visible'});check('one account defaults to form',await p.locator('.tp-account-row').count()===0);await p.getByRole('button',{name:'Chọn tài khoản',exact:true}).click();await p.getByRole('button',{name:'Dùng tài khoản khác',exact:true}).click();check('other account clears login',await p.locator('[name=login]').inputValue()==='');
 await p.locator('[name=login]').focus();for(let i=0;i<4&&!await p.locator('[name=password]').evaluate(e=>e===document.activeElement);i++)await p.keyboard.press('Tab');check('Tab reaches password',await p.locator('[name=password]').evaluate(e=>e===document.activeElement));
 await p.emulateMedia({reducedMotion:'reduce'});check('reduced motion login',await p.locator('.tp-auth-content').evaluate(e=>getComputedStyle(e).animationName)==='none');
 await p.setViewportSize({width:720,height:450});await overflow(p,'200 percent equivalent login');await shot(p,'login-zoom200');
 check('native form hooks',await p.locator('form.oe_login_form').evaluate(e=>e.method==='post'&&e.dataset.captcha==='login'&&!!e.querySelector('[name=csrf_token]').value&&e.querySelector('[name=login]').autocomplete==='username'));
}finally{await c.close();current=null}}
async function roles(b){for(const[alias,a]of Object.entries(actors)){const[c,p]=await context(b);try{
 await login(p,a);check(alias+' authenticated',!!(await info(c)).uid);
 await p.goto(base+'/odoo/action-tp_web_home.action_home');await p.locator('.o_tp_web_home').waitFor();check(alias+' one Home',await p.locator('.o_tp_web_home_button').count()===1);check(alias+' navbar56',await p.locator('.tp-shell-navbar').evaluate(e=>Math.round(e.getBoundingClientRect().height))===56);
 if(alias==='admin')await shot(p,'home-1440');
 await p.goto(base+'/odoo/action-tp_kd_workspace.action_overview');await p.locator('.o_tp_kd_ov').waitFor({timeout:60000});check(alias+' sidebar',await p.locator('.o_tp_kd_sidebar').isVisible());
 if(alias==='admin'){
  for(const[w,h]of[[1440,900],[1280,800],[768,1024],[390,844],[320,844]]){await p.setViewportSize({width:w,height:h});await overflow(p,'navbar overview '+w);await shot(p,'overview-'+w)}
  await p.setViewportSize({width:1440,height:900});await p.getByRole('button',{name:'Thu gọn thanh bên',exact:true}).click();await p.locator('.o_tp_kd_sidebar.is-rail').waitFor();await shot(p,'rail');await p.getByRole('button',{name:'Mở rộng thanh bên',exact:true}).click();
  await p.locator('.o_tp_kd_sidebar').getByRole('link',{name:'Năng lực và chứng chỉ',exact:true}).click();await p.locator('.o_list_view .o_list_renderer').waitFor();await shot(p,'list-1440');
  await p.locator('.o_data_row').first().click();await p.locator('.o_form_view').waitFor();await shot(p,'form-1440');
  await p.locator('.o_tp_web_home_button').click();await p.locator('.o_tp_web_home').waitFor();check('Home route native action',/tp-home|tp_web_home/.test(p.url()));
  await p.goto(base+'/odoo/project');await p.locator('.o_control_panel').waitFor();await shot(p,'native-project');check('native app has real context',!!await p.locator('.o_menu_brand').innerText());
  await p.locator('.o_navbar_apps_menu button').click();await p.locator('.o-dropdown--menu').waitFor({state:'visible'});check('native apps dropdown opens',await p.locator('.o-dropdown--menu').isVisible());await p.keyboard.press('Escape');
 }
 await p.setViewportSize({width:390,height:844});await p.goto(base+'/odoo/action-tp_kd_workspace.action_overview');await p.locator('.o_tp_kd_ov').waitFor();await p.locator('.o_tp_kd_menu_toggle').click();await p.locator('.o_tp_kd_sidebar.is-drawer').waitFor();check(alias+' mobile drawer',true);await p.keyboard.press('Escape');await p.locator('.o_tp_kd_sidebar.is-drawer').waitFor({state:'hidden'});await p.waitForFunction(()=>document.activeElement?.classList.contains('o_tp_kd_menu_toggle'));
 await p.locator('.o_mobile_menu_toggle').click();await p.locator('.o_burger_menu').waitFor();await p.waitForFunction(()=>document.activeElement?.closest('.o_burger_menu'));await p.keyboard.press('Escape');await p.locator('.o_burger_menu').waitFor({state:'hidden'});await p.waitForFunction(()=>document.activeElement?.classList.contains('o_mobile_menu_toggle'));check(alias+' burger focus',await p.locator('.o_mobile_menu_toggle').evaluate(e=>e===document.activeElement));
 await p.setViewportSize({width:1440,height:900});await p.locator('.o_user_menu').click();check(alias+' user menu name',!!await p.locator('.tp-shell-user-heading strong').innerText());check(alias+' native preferences retained',await p.locator('[data-menu=preferences]').isVisible());await shot(p,alias+'-user-menu');await p.keyboard.press('Escape');
 await logout(p);check(alias+' session ended',!(await info(c))?.uid);check(alias+' protected me 401',(await c.request.get(base+'/api/v1/me')).status()===401);
 await p.goBack();await p.reload();check(alias+' Back refresh session remains ended',!(await info(c))?.uid);
 await p.goto(base+'/odoo/action-tp_kd_workspace.action_overview');await p.locator('.tp-native-login').waitFor();check(alias+' deep link protected',!await p.locator('.o_tp_kd_ov').count());
 if(alias==='admin')await shot(p,'logout');
}finally{await c.close();current=null}}}
function totp(secret){const bits=secret.replace(/=/g,'').split('').map(c=>'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'.indexOf(c).toString(2).padStart(5,'0')).join('');const key=Buffer.from(bits.match(/.{8}/g).map(s=>parseInt(s,2)));const counter=Buffer.alloc(8);counter.writeBigUInt64BE(BigInt(Math.floor(Date.now()/30000)));const d=crypto.createHmac('sha1',key).update(counter).digest(),o=d[19]&15;return String((d.readUInt32BE(o)&0x7fffffff)%1000000).padStart(6,'0')}
async function mfa(b){if(target!=='clone')return;const fixture=read('.local/ui-shell-auth001/fixture.json');assert(fixture.database===owner.database);const[c,p]=await context(b);try{
 const partial=async()=>{await p.goto(base+'/web/login?redirect='+encodeURIComponent('/odoo/action-tp_web_home.action_home'));await p.locator('[name=login]').fill(fixture.login);await p.locator('[name=password]').fill(fixture.password);await p.locator('[name=password]').press('Enter');await p.locator('[name=totp_token]').waitFor()};
 await partial();check('TOTP keeps native fields',await p.locator('[name=totp_token]').getAttribute('autocomplete')==='one-time-code');await p.locator('[name=totp_token]').fill('invalid-format');await p.locator('[name=totp_token]').press('Enter');await p.locator('.alert-danger').waitFor();check('TOTP error shown',await p.locator('.alert-danger').innerText()!=='');await shot(p,'totp-error');
 await p.locator('[name=remember]').check();await p.locator('[name=totp_token]').fill(totp(fixture.totp_secret));await p.locator('[name=totp_token]').press('Enter');await p.locator('.o_web_client').waitFor({timeout:60000});check('TOTP success native deep link',(await info(c)).uid===fixture.uid);const trusted=(await c.cookies()).find(x=>x.name==='td_id');check('trusted device native HttpOnly cookie',trusted?.httpOnly&&trusted.sameSite==='Lax');await logout(p);
 await login(p,fixture);check('trusted device native bypass of second factor',(await info(c)).uid===fixture.uid);await logout(p);await c.clearCookies({name:'td_id'});
 await partial();for(const w of[1440,390]){await p.setViewportSize({width:w,height:w===1440?900:844});await overflow(p,'TOTP '+w);await shot(p,'totp-'+w)}await p.getByRole('button',{name:'Hủy và quay lại',exact:true}).click();await p.locator('.tp-native-login').waitFor();check('TOTP cancel safe native login',new URL(p.url()).pathname==='/web/login'&&!(await info(c))?.uid);
}finally{await c.close();current=null}}
(async()=>{const b=await chromium.launch({headless:true});try{await authScreens(b);await roles(b);await mfa(b);check('source unchanged during browser',JSON.stringify(hashes())===JSON.stringify(initial));}catch(e){failures.push(redact(e.stack||e.message));if(current&&!current.isClosed())await shot(current,'failure').catch(()=>{});}finally{await b.close();const result={ok:!failures.length&&!errors.length,target,checks,failures,errors,source_hashes:initial,time:new Date().toISOString()};fs.writeFileSync(path.join(local,target+'-browser.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({ok:result.ok,target,checks:checks.length,failures,errors}));process.exitCode=result.ok?0:1}})();
