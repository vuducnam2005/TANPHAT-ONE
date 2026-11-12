/* Supplemental live UI checks. All identities and screenshots stay private. */
const {chromium}=require('../frontend/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),local=path.join(root,'.local/ui-shell-auth001');
const target=process.argv[2]||'clone';assert(['clone','dev'].includes(target));
const base=`http://127.0.0.1:${target==='dev'?18069:19189}`;
const checks=[],errors=[];
const check=(name,value)=>{assert(value,name);checks.push(name)};
(async()=>{const b=await chromium.launch({headless:true});const c=await b.newContext({viewport:{width:1440,height:900},locale:'vi-VN'}),p=await c.newPage();try{
 p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await p.goto(base+'/web/login');await p.locator('[name=login]').waitFor({state:'visible'});
 const submit=p.locator('form.oe_login_form button[type=submit]');
 await p.mouse.move(2,2);const normal=await submit.evaluate(e=>getComputedStyle(e).backgroundColor);
 await submit.hover();await p.waitForFunction(([selector,old])=>getComputedStyle(document.querySelector(selector)).backgroundColor!==old,['form.oe_login_form button[type=submit]',normal]);check('login hover visibly changes',true);
 await submit.focus();check('keyboard focus visible',await submit.evaluate(e=>getComputedStyle(e).outlineStyle!=='none'));
 for(const [route,title] of [['/web/signup','Tạo tài khoản'],['/web/reset_password','Đặt lại mật khẩu']]){
  const a=p.getByRole('link',{name:route==='/web/signup'?'Tạo tài khoản':'Quên mật khẩu?',exact:true});
  if(await a.count()){
   await p.goto(base+route);await p.getByRole('heading',{name:title,exact:true}).waitFor();
   check(route+' native form retained',await p.locator('.tp-native-login form').evaluate(e=>e.method==='post'&&!!e.querySelector('[name=csrf_token]')&&!!e.dataset.captcha));
   for(const width of [1440,390]){await p.setViewportSize({width,height:width===1440?900:844});check(route+' '+width+' no overflow',await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await p.screenshot({path:path.join(local,'shots',target,(route==='/web/signup'?'signup':'reset')+'-'+width+'.png')});}
   await p.setViewportSize({width:1440,height:900});await p.goto(base+'/web/login');await p.locator('[name=login]').waitFor({state:'visible'});
  }
 }
 await p.evaluate(()=>localStorage.setItem('web.lastConnectedUser',JSON.stringify([
  {login:'synthetic.one',name:'Tài khoản kiểm thử',partnerId:0,userId:9001},
  {login:'synthetic.two',name:'Tài khoản khác',partnerId:0,userId:9002}
 ])));
 await p.route(/\/web\/image\/res\.partner\/0\/avatar_128/,r=>r.fulfill({status:200,contentType:'image/png',body:'invalid-image'}));
 await p.reload();await p.locator('.tp-account-row').first().waitFor();
 await p.waitForFunction(()=>[...document.querySelectorAll('.tp-account-avatar img')].every(e=>e.hidden));
 check('broken avatar exposes initial fallback',await p.locator('.tp-account-avatar > span').first().isVisible());
 await p.unroute(/\/web\/image\/res\.partner\/0\/avatar_128/);
 await p.getByRole('button',{name:'Dùng tài khoản khác',exact:true}).click();
 await p.locator('[name=login]').fill('admin');await p.locator('[name=password]').fill(JSON.parse(fs.readFileSync(path.join(root,'.local/dev-secrets.json'))).admin);await p.locator('[name=password]').press('Enter');await p.locator('.o_web_client').waitFor({timeout:60000});
 await p.goto(base+'/odoo/tp-home');await p.locator('.o_tp_web_home').waitFor();
 const home=p.locator('.o_navbar_apps_menu button');await p.mouse.move(2,2);const old=await home.evaluate(e=>getComputedStyle(e).backgroundColor);
 await home.hover();await p.waitForFunction(old=>getComputedStyle(document.querySelector('.o_navbar_apps_menu button')).backgroundColor!==old,old);check('navbar hover visibly changes',true);
 await p.emulateMedia({reducedMotion:'reduce'});check('navbar reduced motion',await home.evaluate(e=>getComputedStyle(e).transitionDuration)==='0s');
 const company=p.locator('.o_switch_company_menu');check('company keeps full native title',!!await company.getAttribute('title'));check('company label constrained',await company.evaluate(e=>getComputedStyle(e).textOverflow)==='ellipsis');
 for(const icon of ['forum','schedule']){
  const toggle=p.locator(`.o_menu_systray button:has([data-icon="${icon}"])`);await toggle.click();await p.locator('.o-dropdown--menu').waitFor({state:'visible'});check(icon+' native systray opens',true);await toggle.click();await p.locator('.o-dropdown--menu').waitFor({state:'hidden'});
 }
 await p.setViewportSize({width:390,height:844});await p.locator('.o_mobile_menu_toggle').waitFor();await p.screenshot({path:path.join(local,'shots',target,'home-390.png')});await p.locator('.o_mobile_menu_toggle').click();await p.locator('.o_user_menu_mobile').waitFor();const mobileLogout=p.locator('.o_user_menu_mobile a').filter({hasText:/Đăng xuất|Log out/});await mobileLogout.waitFor();check('phone native account menu accessible',true);
 await p.screenshot({path:path.join(local,'shots',target,'mobile-user-menu.png')});
 const response=p.waitForResponse(r=>r.url().includes('/web/session/logout')&&r.request().method()==='POST');await mobileLogout.click();await response;await p.locator('.tp-native-login').waitFor();check('phone logout protected API 401',(await c.request.get(base+'/api/v1/me')).status()===401);
 check('no console or page errors',!errors.length);
 const report={ok:true,target,checks,errors,time:new Date().toISOString()};fs.writeFileSync(path.join(local,`details-${target}.json`),JSON.stringify(report,null,2));console.log(JSON.stringify({ok:true,target,checks:checks.length}));
 }catch(e){const report={ok:false,target,checks,errors,error:String(e)};fs.writeFileSync(path.join(local,`details-${target}.json`),JSON.stringify(report,null,2));console.log(JSON.stringify(report));process.exitCode=1}finally{await b.close()}})();
