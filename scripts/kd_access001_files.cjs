/* Real HTTP file access for five scoped clone accounts; no dev fixture creation. */
const {request}=require('../frontend/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const local=path.resolve(__dirname,'../.local/kd-access001');
const fixture=JSON.parse(fs.readFileSync(path.join(local,'file-fixture.json')));
const credentials=JSON.parse(fs.readFileSync(path.join(local,'clone-credentials.json')));
const delta=JSON.parse(fs.readFileSync(path.join(local,'clone-delta.json')));
const phase=process.argv[2]||'normal'; assert(['normal','revoked','expired','unassigned'].includes(phase));
const base='http://127.0.0.1:18989',checks=[];
(async()=>{
 for(const [alias,credential] of Object.entries(credentials)){
  const c=await request.newContext();
  try {
   const login=await (await c.post(base+'/web/session/authenticate',{data:{jsonrpc:'2.0',method:'call',params:{db:delta.identity.database,...credential}}})).json();
   assert(login.result?.uid===delta.users[alias].id,'identity mismatch');
   const allowed=['head','deputy','planning'].includes(alias)&&!(alias==='head'&&phase!=='normal');
   for(const url of [`/web/content/tp.contract.document/${fixture.document_id}/file?download=true`,...fixture.attachment_ids.map(id=>`/web/content/${id}?download=true`)]){
    const response=await c.get(base+url),body=await response.body();
    if(allowed)assert(response.status()===200&&crypto.createHash('sha256').update(body).digest('hex')===fixture.content_sha256,alias+' file should be readable');
    else assert([403,404].includes(response.status())&&!body.includes(Buffer.from('987654321')),alias+' file must be denied');
    checks.push(alias+' '+phase+' '+(allowed?'allow':'deny')+' HTTP file');
   }
   const rpc=await (await c.post(base+'/web/dataset/call_kw/tp.contract.document/read',{data:{jsonrpc:'2.0',method:'call',params:{model:'tp.contract.document',method:'read',args:[[fixture.document_id],['file','file_name']],kwargs:{}}}})).json();
   assert(allowed?!rpc.error:Boolean(rpc.error),alias+' RPC file permission');
   checks.push(alias+' '+phase+' RPC file');
  }finally{await c.dispose();}
 }
 fs.writeFileSync(path.join(local,`clone-files-${phase}.json`),JSON.stringify({passed:checks.length,checks},null,2));
 console.log(JSON.stringify({phase,passed:checks.length}));
})().catch(e=>{console.error(e.message);process.exitCode=1;});
