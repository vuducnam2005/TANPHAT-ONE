import { describe, expect, test } from "@odoo/hoot";
import { donutSegments, barWidth } from "@tp_reporting/dashboard";
describe("Reporting chart semantics",()=>{
 test("donut uses obligation denominator and preserves exact drill domain",()=>{const domain=[["id","in",[3,8]]];const result=donutSegments([{key:"submitted",count:2,domain},{key:"pending",count:3}],5);expect(result[0].length).toBe(40);expect(result[1].offset).toBe(40);expect(result[1].length).toBe(60);expect(result[0].domain).toEqual(domain);});
 test("zero denominator is empty rather than fabricated shares",()=>{expect(donutSegments([{count:0}],0)[0].length).toBe(0);});
 test("same unit bars share scale and preserve missing actual",()=>{expect(barWidth(50,100,50)).toBe(50);expect(barWidth(100,100,50)).toBe(100);expect(barWidth(null,100,null)).toBe(0);expect(barWidth(0,0,0)).toBe(0);expect(barWidth(125,100,125)).toBe(100);});
});
import { ReportingFormController } from "@tp_reporting/form";
describe("Reporting native form concurrency",()=>{
 test("loaded version travels through native save context",async()=>{let captured;const controller={model:{_updateConfig:async(config,patch,options)=>{captured={config,patch,options};}}};const record={resId:42,resModel:"tp.report.document",data:{version:7},context:{allowed_company_ids:[1]},config:{}};await ReportingFormController.prototype.onWillSaveRecord.call(controller,record,{});expect(captured.patch.context.tp_reporting_expected_version).toBe(7);expect(captured.patch.context.allowed_company_ids).toEqual([1]);expect(captured.options.reload).toBe(false);});
 test("line save uses parent document token",async()=>{let token;const controller={model:{_updateConfig:async(config,patch)=>{token=patch.context.tp_reporting_expected_version;}}};await ReportingFormController.prototype.onWillSaveRecord.call(controller,{resId:3,resModel:"tp.report.line",data:{document_version:9},context:{},config:{}},{});expect(token).toBe(9);});
 test("new record does not claim existing server version",async()=>{let calls=0;const controller={model:{_updateConfig:async()=>calls++}};await ReportingFormController.prototype.onWillSaveRecord.call(controller,{resId:false,resModel:"tp.report.document",data:{version:1}},{});expect(calls).toBe(0);});
});
import { ReportingDashboard } from "@tp_reporting/dashboard";
describe("Reporting dashboard session boundaries",()=>{
 test("expired session clears data and propagates to native login dialog",async()=>{
  const expired={exceptionName:"odoo.http.session.SessionExpiredException"};
  const context={seq:0,state:{date_start:"2026-10-01",date_end:"2026-12-31",period_type:"quarter",department_id:"",data:{private:true}},orm:{call:async()=>{throw expired;}}};
  let error;try{await ReportingDashboard.prototype.load.call(context);}catch(e){error=e;}
  expect(error).toBe(expired);expect(context.state.data).toBe(null);expect(context.state.busy).toBe(false);
 });
 test("older response cannot overwrite a newer dashboard query",async()=>{
  let finish;const first=new Promise(resolve=>finish=resolve);let calls=0;
  const context={seq:0,state:{date_start:"2026-10-01",date_end:"2026-12-31",period_type:"quarter",department_id:"",data:null},orm:{call:async()=>++calls===1?first:{period:"new"}}};
  const old=ReportingDashboard.prototype.load.call(context);await ReportingDashboard.prototype.load.call(context);finish({period:"old"});await old;expect(context.state.data.period).toBe("new");
 });
});
import { ReportingReviewerField } from "@tp_reporting/reviewer";
import { ReportingPersonField } from "@tp_reporting/person";
describe("Reporting scoped identity choices",()=>{
 test("reviewer update uses canonical user ID and label returned by scoped server",async()=>{let update;const controller={state:{choices:[{id:12,display_name:"Người rà trong quyền"}]},props:{name:"reviewer_id",record:{update:async values=>update=values}}};await ReportingReviewerField.prototype.change.call(controller,{target:{value:"12"}});expect(update).toEqual({reviewer_id:{id:12,display_name:"Người rà trong quyền"}});});
 test("unknown injected selection cannot fabricate a reviewer",async()=>{let update;const controller={state:{choices:[{id:12,display_name:"Người rà"}]},props:{name:"reviewer_id",record:{update:async values=>update=values}}};await ReportingReviewerField.prototype.change.call(controller,{target:{value:"999"}});expect(update).toEqual({reviewer_id:false});});
 test("people selection is an ID update rather than a parallel identity record",async()=>{let update;const controller={state:{choices:[{id:4,display_name:"Người phụ trách"}]},props:{name:"owner_id",record:{update:async values=>update=values}}};await ReportingPersonField.prototype.select.call(controller,{target:{value:"4"}});expect(update.owner_id.id).toBe(4);});
});
