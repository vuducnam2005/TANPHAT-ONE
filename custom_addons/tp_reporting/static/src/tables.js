import { Component, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { useSetupAction } from "@web/search/action_hook";
import { useService } from "@web/core/utils/hooks";
import { render } from "@web/owl2/utils";
import { TpTableFilterBar } from "@tp_web_home/search/table_filter_bar";
import { registerTableFilterProfile } from "@tp_web_home/search/filter_domain";
const c = (field,label,type="char") => ({key:field,field,label,type,...(["selection"].includes(type)?{multi:true}:{})});
const common = [c("name","Nội dung"),c("department_id","Phòng ban","many2one"),c("owner_id","Người phụ trách","many2one"),c("period_type","Loại kỳ","selection"),c("state","Trạng thái","selection"),c("date_start","Ngày bắt đầu","date"),c("date_end","Ngày kết thúc","date")];
export const REPORT_FILTERS = {
 "tp.report.plan": [...common,c("parent_id","Kế hoạch cha","many2one"),c("project_id","Dự án","many2one"),c("deadline","Hạn hoàn thành","datetime")],
 "tp.report.document": [...common,c("level","Cấp báo cáo","selection"),c("template_id","Mẫu","many2one"),c("deadline","Hạn nộp","datetime")],
 "tp.report.line": [c("name","Công việc"),c("work_status","Trạng thái việc","selection"),c("priority","Ưu tiên","selection"),c("work_deadline","Hạn công việc","date"),c("document_id","Báo cáo","many2one"),c("project_id","Dự án","many2one"),c("plan_id","Kế hoạch","many2one"),c("work_date","Ngày thực hiện","date")],
};
for(const [model,criteria] of Object.entries(REPORT_FILTERS)) registerTableFilterProfile(model,{criteria:criteria.slice(0,5)});
export class ReportTableTools extends Component {
 static template="tp_reporting.TableTools";
 props=useProps();
 state=proxy({busy:false,error:""});
 sizes=[10,20,50,100];
 setup(){this.action=useService("action");}
 inbox(){return this.action.doAction("tp_reporting.action_my_review");}
 obligations(){return this.action.doAction("tp_reporting.action_obligations");}
 async exportXlsx(){if(this.state.busy)return;this.state.busy=true;this.state.error="";try{await download({url:"/tp_reporting/export",data:{format:"xlsx",domain:JSON.stringify(this.props.controller.model.root.domain)}});}catch{this.state.error="Không xuất được báo cáo. Vui lòng thử lại.";}finally{this.state.busy=false;}}
 async changeSize(ev){
  const ctrl=this.props.controller, limit=Number(ev.target.value);
  if(this.state.busy || ctrl.editedRecord || !this.sizes.includes(limit))return;
  this.state.busy=true; this.state.error="";
  try {await ctrl.model.root.load({limit,offset:0});render(ctrl);}
  catch {this.state.error="Không tải được trang. Vui lòng thử lại.";ev.target.value=String(ctrl.model.root.limit);}
  finally {this.state.busy=false;}
 }
}
export class ReportingListController extends ListController {
 static template="tp_reporting.ListView";
 static components={...ListController.components,ReportTableTools,TpTableFilterBar};
 get className(){return `${super.className || ""} tp_reporting_list`;}
 setup(){super.setup();useSetupAction({getGlobalState:()=>({tpReportList:{limit:this.model.root.limit,offset:this.model.root.offset,orderBy:this.model.root.orderBy.map(x=>({...x}))}})});}
 get modelParams(){const p=super.modelParams;if(this.props.state?.modelState)return p;const saved=this.props.globalState?.tpReportList;return saved&&[10,20,50,100].includes(saved.limit)?{...p,config:{...p.config,...saved}}:{...p,limit:100};}
 clearReportFilters(){this.env.searchModel.clearQuery();}
 advancedReportFilters(){this.rootRef?.()?.querySelector(".o_searchview_dropdown_toggler")?.click();}
}
registry.category("views").add("tp_reporting_list",{...listView,Controller:ReportingListController});
import "./filter_profiles";
