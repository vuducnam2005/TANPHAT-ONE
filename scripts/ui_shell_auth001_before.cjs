/* Private before evidence: read-only UI navigation on the existing dev. */
const {chromium}=require('../frontend/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),out=path.join(root,'.local/ui-shell-auth001/shots/before');
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const actors=read('.local/kd-access001/dev-credentials.json');
actors.admin={login:'admin',password:read('.local/dev-secrets.json').admin};
const base='http://127.0.0.1:18069';
(async()=>{fs.mkdirSync(out,{recursive:true});const b=await chromium.launch({headless:true});try{
 const c=await b.newContext({viewport:{width:1440,height:900},locale:'vi-VN'}),p=await c.newPage();
 await p.goto(base+'/web/login');await p.locator('[name=login]').waitFor({state:'visible'});
 await p.screenshot({path:path.join(out,'login-1440.png')});
 await p.setViewportSize({width:390,height:844});await p.screenshot({path:path.join(out,'login-390.png')});
 await p.setViewportSize({width:1440,height:900});
 await p.locator('[name=login]').fill(actors.admin.login);await p.locator('[name=password]').fill(actors.admin.password);await p.locator('button[type=submit]').first().click();await p.locator('.o_web_client').waitFor({timeout:120000});
 for(const [name,route,selector] of [['home','/odoo/action-tp_web_home.action_home','.o_tp_web_home'],['overview','/odoo/action-tp_kd_workspace.action_overview','.o_tp_kd_ov']]){
  await p.goto(base+route);await p.locator(selector).waitFor({timeout:60000});
  for(const width of [1440,390]){await p.setViewportSize({width,height:width===390?844:900});await p.screenshot({path:path.join(out,`${name}-${width}.png`)});}
 }
 // Native remembered entries for chooser screenshots; no credential/session stored.
 await p.evaluate(users=>localStorage.setItem('web.lastConnectedUser',JSON.stringify(users)),[{login:'synthetic.one',name:'Tài khoản kiểm thử tên dài '.repeat(4),partnerId:0,userId:9001,partnerWriteDate:''},{login:'synthetic.two',name:'Tài khoản kiểm thử',partnerId:0,userId:9002,partnerWriteDate:''}]);
 await p.setViewportSize({width:1440,height:900});await p.locator('.o_user_menu').click();await p.locator('[data-menu=logout]').click();await p.locator('.o_user_switch').waitFor({timeout:60000});
 await p.screenshot({path:path.join(out,'chooser-1440.png')});await p.setViewportSize({width:390,height:844});await p.screenshot({path:path.join(out,'chooser-390.png')});
 console.log('BEFORE evidence captured: login/home/overview/chooser desktop+mobile.');
}finally{await b.close();}})().catch(()=>{console.error('Before capture failed; inspect private state.');process.exit(1)});
