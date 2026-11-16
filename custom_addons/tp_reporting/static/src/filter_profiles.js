import { registerTableFilterProfile } from "@tp_web_home/search/filter_domain";
const c=(field,label,type="char")=>({key:field,field,label,type,...(type==="selection"?{multi:true}:{})});
const config={
 "tp.report.section.content":[c("content","Nội dung"),c("section_id","Mục trong mẫu","many2one"),c("design_stage","Bước thiết kế","selection"),c("source_reference","Tham chiếu nguồn")],
 "tp.report.review":[c("comment","Nội dung"),c("document_id","Báo cáo","many2one"),c("line_id","Đầu việc","many2one"),c("actor_id","Người viết","many2one"),c("assessment","Đánh giá","selection"),c("audience","Đối tượng xem","selection"),c("create_date","Thời điểm","datetime")],
 "tp.report.snapshot":[c("name","Phiên bản"),c("document_id","Báo cáo","many2one"),c("kind","Loại bản","selection"),c("create_date","Thời điểm","datetime")],
 "tp.report.event":[c("name","Sự kiện"),c("actor_id","Người thao tác","many2one"),c("document_id","Báo cáo","many2one"),c("plan_id","Kế hoạch","many2one"),c("create_date","Thời điểm","datetime")],
 "tp.report.obligation":[c("name","Nghĩa vụ"),c("owner_id","Người nộp","many2one"),c("department_id","Phòng ban","many2one"),c("period_type","Loại kỳ","selection"),c("date_start","Từ ngày","date"),c("deadline","Hạn nộp","datetime"),c("status","Tình trạng nộp","selection")],
 "tp.report.template":[c("name","Mẫu"),c("code","Mã"),c("level","Cấp báo cáo","selection"),c("period_type","Loại kỳ","selection"),c("active","Đang áp dụng","boolean")],
 "tp.report.section":[c("name","Mục"),c("template_id","Mẫu","many2one"),c("audience","Đối tượng xem","selection"),c("required","Bắt buộc","boolean")],
 "tp.report.assignment":[c("name","Phân công"),c("user_id","Tài khoản","many2one"),c("department_id","Phòng ban","many2one"),c("capability","Năng lực","selection"),c("date_start","Hiệu lực từ","date"),c("date_end","Hiệu lực đến","date"),c("active","Đang áp dụng","boolean")],
 "tp.report.schedule":[c("name","Lịch"),c("department_id","Phòng ban","many2one"),c("period_type","Loại kỳ","selection"),c("active","Đang áp dụng","boolean")],
 "tp.report.metric":[c("name","Chỉ tiêu"),c("code","Mã"),c("method","Cách tính","selection"),c("unit","Đơn vị"),c("currency_id","Tiền tệ","many2one")],
 "tp.report.value":[c("name","Giá trị"),c("document_id","Báo cáo","many2one"),c("metric_id","Chỉ tiêu","many2one"),c("status","Tình trạng nguồn","selection"),c("source_date","Ngày nguồn","date"),c("provider_id","Người cung cấp","many2one")],
 "tp.report.directive":[c("name","Nội dung"),c("owner_id","Người nhận","many2one"),c("department_id","Phòng ban","many2one"),c("deadline","Hạn xử lý","datetime"),c("state","Trạng thái","selection"),c("document_id","Báo cáo nguồn","many2one")]
};
for(const [model,criteria] of Object.entries(config))registerTableFilterProfile(model,{criteria:criteria.slice(0,5)});
