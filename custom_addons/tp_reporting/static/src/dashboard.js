import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { deserializeDate, deserializeDateTime, formatDate, formatDateTime } from "@web/core/l10n/dates";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";
export function donutSegments(items,total){let offset=0;return items.map(item=>{const length=total>0?item.count/total*100:0;const segment={...item,length,offset};offset+=length;return segment;});}
export function barWidth(value,plan,actual){const max=Math.max(Number(plan)||0,Number(actual)||0);return value===null||max<=0?0:Math.max(0,Number(value))/max*100;}
export class ReportingDashboard extends Component {
 static template="tp_reporting.Dashboard";
 setup(){useProps(standardActionServiceProps);this.orm=useService("orm");this.action=useService("action");this.seq=0;const d=new Date(), y=d.getFullYear(),q=Math.floor(d.getMonth()/3);const iso=x=>`${x.getFullYear()}-${String(x.getMonth()+1).padStart(2,"0")}-${String(x.getDate()).padStart(2,"0")}`;this.state=proxy({busy:true,error:"",data:null,date_start:iso(new Date(y,q*3,1)),date_end:iso(new Date(y,q*3+3,0)),period_type:"quarter",department_id:""});onWillStart(()=>this.load());}
 async load(){const seq=++this.seq;this.state.error="";if(!this.state.date_start||!this.state.date_end||this.state.date_start>this.state.date_end){this.state.error="Ngày bắt đầu phải trước hoặc bằng ngày kết thúc.";this.state.busy=false;return;}this.state.busy=true;try {const data=await this.orm.call("tp.report.dashboard","get_data",[this.state.date_start,this.state.date_end,this.state.period_type,Number(this.state.department_id)||false]);if(seq===this.seq)this.state.data=data;}catch(e){if(seq===this.seq)this.state.data=null;if(["odoo.http.session.SessionExpiredException","werkzeug.exceptions.Forbidden"].includes(e.exceptionName||e.data?.name))throw e;if(seq===this.seq)this.state.error=e.data?.name?.includes("AccessError")?"Bạn không có quyền xem phạm vi này.":"Không tải được báo cáo. Vui lòng thử lại.";}finally{if(seq===this.seq)this.state.busy=false;}}
 get segments(){return donutSegments(this.state.data?.submission?.items||[],this.state.data?.submission?.total||0);}
 date(v){if(!v)return "Chưa đặt hạn";return v.length>10?formatDateTime(deserializeDateTime(v)):formatDate(deserializeDate(v));}
 format(v){return v===null||v===undefined?"Chưa có nguồn":new Intl.NumberFormat("vi-VN",{maximumFractionDigits:2}).format(v);}
 width(v,row){return barWidth(v,row.plan,row.actual);}
 open(item){if(!item.model||!Array.isArray(item.domain))return;return this.action.doAction({type:"ir.actions.act_window",name:item.label||item.name||"Chi tiết báo cáo",res_model:item.model,views:[[false,"list"],[false,"form"]],domain:item.domain,context:{...(item.context||{}),tp_reporting_scope:true}});}
 openDecision(item){return this.action.doAction({type:"ir.actions.act_window",name:item.name,res_model:item.model||"tp.report.directive",res_id:item.id,views:[[false,"form"]]});}
}
registry.category("actions").add("tp_reporting.dashboard",ReportingDashboard);
