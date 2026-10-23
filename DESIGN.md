---
version: alpha
name: Tadic Management
description: Giao diện nền cho hệ thống quản trị nội bộ trong giai đoạn khảo sát.
colors:
  navy: "#17344A"
  ink: "#172D3E"
  muted: "#566B79"
  accent: "#08786F"
  canvas: "#F4F7F8"
  surface: "#FFFFFF"
  line: "#D9E2E6"
  ready: "#17634C"
  pending: "#795B21"
typography:
  heading:
    fontFamily: Be Vietnam Pro
    fontSize: 2.375rem
    fontWeight: 700
    lineHeight: 1.32
  section:
    fontFamily: Be Vietnam Pro
    fontSize: 1.25rem
    fontWeight: 700
    lineHeight: 1.4
  body:
    fontFamily: Be Vietnam Pro
    fontSize: 0.8125rem
    fontWeight: 400
    lineHeight: 1.8
rounded:
  sm: 4px
  md: 8px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
---

## Overview

Tadic Management là công cụ làm việc nội bộ. Giao diện ưu tiên khả năng tìm, đọc và cập nhật thông tin nghiệp vụ nhanh. Bản Tuần 1 là khung giao diện, chưa xác định màn hình chức năng của P.KHKD và Ban quản trị.

## Colors

Nền sáng và nét kẻ mảnh giúp danh sách dài dễ đọc. Navy giữ vai trò điều hướng, accent xanh ngọc đánh dấu thao tác chính và điểm đang chú ý. Trạng thái hoàn thành và trạng thái chờ dùng màu riêng, luôn có nhãn chữ đi kèm. Đây là bảng màu tạm cho bản mẫu, cần đối chiếu bộ nhận diện Tadic nếu được cung cấp.

## Typography

Be Vietnam Pro được đóng gói cùng frontend để hiển thị tiếng Việt ổn định cả khi không có mạng. Tiêu đề đậm, ngắn; nội dung có khoảng dòng thoáng để đọc biểu mẫu và bảng. Dùng chữ thường theo câu, tránh nhãn viết hoa toàn bộ.

## Layout

Trên màn hình rộng, thanh điều hướng cố định ở trái và nội dung ở phải. Nội dung dùng hàng có đường phân cách, không dựa vào nhiều thẻ nổi. Trên màn hình hẹp, điều hướng chuyển lên đầu trang, các hàng thông tin xếp dọc và vẫn giữ nhãn trạng thái.

## Components

- Button: một hành động chính rõ ràng trong mỗi vùng; hành động phụ ít nổi bật hơn.
- StatusBadge: nhãn chữ bắt buộc, màu chỉ hỗ trợ nhận biết.
- Search: trường tìm kiếm có nhãn, phản hồi khi không có kết quả và nút xóa từ khóa.
- List row: tên hạng mục, thông tin hỗ trợ và trạng thái theo cùng thứ tự ở mọi màn hình.

## Accessibility

Điều hướng bằng bàn phím phải nhìn thấy tiêu điểm. Nút và liên kết có tên rõ nghĩa. Tôn trọng thiết lập giảm chuyển động; không dùng màu làm tín hiệu duy nhất. Mọi màn hình cần kiểm tra ở kích thước máy tính và điện thoại.

## Content

Chỉ hiển thị trạng thái khi có bằng chứng. Phân biệt dữ liệu mẫu với dữ liệu đã đồng bộ. Ghi rõ nội dung nào còn chờ phòng ban xác nhận trước khi biến thành chức năng chính thức.
