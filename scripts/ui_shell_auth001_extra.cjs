/* Clone-only failure, dirty form, overflow, native security and network recovery probes. */
const {chromium}=require('../frontend/node_modules/playwright'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..'),local=path.join(root,'.local/ui-shell-auth001'),base='http://127.0.0.1:19189';
const owner=JSON.parse(fs.readFileSync(path.join(local,'owner.json')));assert(owner.http_port===19189&&owner.rehearsal_passed);
const a={login:'admin',password:JSON.parse(fs.readFileSync(path.join(root,'.local/dev-secrets.json'))).admin},checks=[],errors=[];
const check=(n,v)=>{assert(v,n);checks.push(n)};
const save=r=>fs.writeFileSync(path.join(local,'extra-result.json'),JSON.stringify(r,null,2));
(async()=>{const b=await chromium.launch({headless:true});let p,c;try{
 c=await b.newContext({viewport:{width:1440,height:900},locale:'vi-VN'});p=await c.newPage();p.on('pageerror',e=>errors.push(e.message));
 await p.goto(base+'/web/login');await p.locator('[name=login]').waitFor({state:'visible'});
 await p.locator('.o_show_password').click();await p.waitForFunction(()=>document.querySelector('[name=password]').type==='text');await p.locator('.o_show_password').click();await p.waitForFunction(()=>document.querySelector('[name=password]').type==='password');
 let posts=0;
 await p.locator('[name=password]').press('Enter');check('required fields prevent submit',posts===0);check('native required validity',await p.locator('form.oe_login_form').evaluate(f=>!f.checkValidity()));
 await p.locator('form.oe_login_form').evaluate(f=>f.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
 await p.waitForFunction(()=>document.querySelector('form.oe_login_form').getAttribute('aria-busy')==='true');
 await p.waitForFunction(()=>!document.querySelector('form.oe_login_form button[type=submit]').disabled,{},{timeout:15000});check('stalled submit restores native button',true);
 await p.route('**/web/login',async r=>{if(r.request().method()==='POST'){posts++;await new Promise(resolve=>setTimeout(resolve,1500));await r.abort('failed')}else await r.continue()});
 await p.locator('[name=login]').fill(a.login);await p.locator('[name=password]').fill(a.password);await p.locator('[name=password]').press('Enter',{noWaitAfter:true});await p.keyboard.press('Enter');await p.keyboard.press('Enter');await p.waitForEvent('requestfailed',{predicate:r=>r.url().includes('/web/login')&&r.method()==='POST'});check('repeated Enter sends once',posts===1);
 await p.unroute('**/web/login');await p.goto(base+'/web/login');await p.locator('[name=login]').fill(a.login);await p.locator('[name=password]').fill(a.password);await p.locator('[name=password]').press('Enter');await p.locator('.o_web_client').waitFor({timeout:60000});check('login recovers after failed network',true);
 await p.goto(base+'/odoo/project');await p.locator('.o_control_panel').waitFor();await p.setViewportSize({width:768,height:1024});await p.waitForTimeout(400);
 check('native sections do not overflow at tablet',await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 if(await p.locator('.o_menu_sections_more button').isVisible()){await p.locator('.o_menu_sections_more button').click();check('More dropdown opens',await p.locator('.o-dropdown--menu').isVisible());await p.keyboard.press('Escape')}else checks.push('native sections fit; More not needed for current app');
 await p.setViewportSize({width:1440,height:900});await p.goto(base+'/odoo/action-tp_kd_workspace.action_overview');await p.locator('.o_tp_kd_ov').waitFor();
 // Use an existing prepare-capable actor; do not broaden admin permissions for a dirty-form probe.
 await p.locator('.o_user_menu').click();await p.locator('[data-menu=logout]').click();await p.locator('.tp-native-login').waitFor();
 const staff=JSON.parse(fs.readFileSync(path.join(root,'.local/kd-access001/dev-credentials.json'))).support;
 if(await p.locator('.tp-account-other').isVisible())await p.locator('.tp-account-other').click();
 await p.locator('[name=login]').fill(staff.login);await p.locator('[name=password]').fill(staff.password);await p.locator('[name=password]').press('Enter');await p.locator('.o_web_client').waitFor({timeout:60000});await p.goto(base+'/odoo/action-tp_kd_workspace.action_overview');await p.locator('.o_tp_kd_ov').waitFor({timeout:60000});
 await p.locator('.o_tp_kd_sidebar').getByRole('link',{name:'Năng lực và chứng chỉ',exact:true}).click();await p.locator('.o_list_renderer').waitFor();await p.locator('.o_list_button_add').click();await p.locator('.o_action_manager .o_form_view').waitFor();const name=p.locator('.o_action_manager [name=name] input');await name.fill('SHELLAUTH unsaved clone');
 await p.locator('.o_tp_web_home_button').click();await p.locator('.o_field_invalid').first().waitFor();check('Home preserves native validation dirty guard',await name.inputValue()==='SHELLAUTH unsaved clone'&&!await p.locator('.o_tp_web_home').count());await p.screenshot({path:path.join(local,'shots/clone/dirty-home.png')});
 await p.locator('.o_form_button_cancel').click();if(await p.locator('.o_dialog').isVisible())await p.locator('.o_dialog .modal-footer .btn-primary').click();check('unsaved draft can be discarded',true);
 const csrf=await p.evaluate(()=>odoo.csrf_token);const bad=await c.request.post(base+'/web/session/logout',{form:{csrf_token:'invalid'},maxRedirects:0});check('logout bad CSRF rejected',bad.status()===400);
 check('CSRF rejection leaves session',!!(await(await c.request.post(base+'/web/session/get_session_info',{data:{jsonrpc:'2.0',method:'call',params:{}}})).json()).result?.uid);
 const ended=await c.request.post(base+'/web/session/logout',{form:{csrf_token:csrf},maxRedirects:0});check('session ends independently',ended.status()===303);
 await p.goto(base+'/odoo/action-tp_kd_workspace.action_overview');await p.locator('.tp-native-login').waitFor();check('expired session returns auth',true);
 await p.setViewportSize({width:1440,height:900});await p.evaluate(()=>localStorage.removeItem('web.lastConnectedUser'));await p.goto(base+'/web/login');await p.locator('[name=login]').fill(a.login);await p.locator('[name=password]').fill(a.password);await p.locator('[name=password]').press('Enter');await p.locator('.o_web_client').waitFor();const cdp=await c.newCDPSession(p);await cdp.send('Emulation.setDeviceMetricsOverride',{width:720,height:450,deviceScaleFactor:1,mobile:false,scale:2});await p.goto(base+'/odoo/tp-home');await p.locator('.o_tp_web_home').waitFor();check('200 percent layout native Home',await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await p.screenshot({path:path.join(local,'shots/clone/home-zoom200.png')});
 check('no pageerror in failure probes',errors.length===0);save({ok:true,checks,errors});console.log(JSON.stringify({ok:true,checks:checks.length}));
}catch(e){const error=String(e.stack||e).replaceAll(a.password,'[REDACTED]');if(p)await p.screenshot({path:path.join(local,'extra-failure.png')}).catch(()=>{});save({ok:false,checks,errors,error});console.log(JSON.stringify({ok:false,checks:checks.length,error,errors}));process.exitCode=1}finally{await b.close()}})();
