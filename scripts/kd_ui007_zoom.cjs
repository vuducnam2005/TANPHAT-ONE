/* Real Chromium page zoom, using the existing disposable-profile technique. */
const fs=require('node:fs'),path=require('node:path');
module.exports=async function(ctx){
 const {chromium,local,out,base,db,actors,check,watch,LEAVES}=ctx;
 const profile=path.join(local,'zoom-profile');
 const c=await chromium.launchPersistentContext(profile,{channel:'chromium',headless:true,viewport:null,args:['--window-size=1440,1000'],locale:'vi-VN'});
 const settings=await c.newPage();
 try {
  await settings.goto('chrome://settings/appearance');await settings.locator('#zoomLevel').waitFor();
  const auth=await(await c.request.post(`${base}/web/session/authenticate`,{data:{jsonrpc:'2.0',method:'call',params:{db,...actors.editor}}})).json();
  if(!auth.result?.uid)throw Error('Zoom login failed');
  const p=await c.newPage();watch(p);
  for(const zoom of [1.25,1.5]){
   await settings.locator('#zoomLevel').selectOption(String(zoom));
   for(const [name,action] of [...LEAVES,['overview','tp_kd_workspace.action_overview']]){
    await p.goto(`${base}/odoo/action-${action}`);await p.locator(name==='overview'?'.o_tp_kd_ov':'.o_list_view').waitFor();
    await p.waitForFunction(n=>Math.abs(devicePixelRatio-n)<0.01,zoom);await ctx.settle(p);
    const geometry=await p.evaluate(()=>({zoom:devicePixelRatio,width:innerWidth,overflow:document.documentElement.scrollWidth-innerWidth}));
    check(`${name} real zoom${zoom*100} no page overflow`,geometry.overflow<=1,geometry);
    const session=await c.newCDPSession(p);const image=await session.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});await session.detach();
    fs.writeFileSync(path.join(out,`${name}-real-zoom${zoom*100}.png`),Buffer.from(image.data,'base64'));
   }
  }
 } finally {await settings.locator('#zoomLevel').selectOption('1').catch(()=>{});await c.close();}
};
