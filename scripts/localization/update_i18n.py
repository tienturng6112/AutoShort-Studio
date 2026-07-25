import json
import os

new_keys = {
    "btn_apply_override": "Apply Override",
    "btn_assign_selected": "Assign Selected",
    "assign_voice": "Assign Voice",
    "lbl_emotion": "Emotion:",
    "msg_extracting_audio": "Extracting audio...",
    "msg_transcribing": "Transcribing...",
    "msg_translating": "Translating...",
    "msg_synthesizing": "Synthesizing voice...",
    "msg_stitching": "Stitching final video...",
    "msg_generating": "Generating...",
    "msg_failed": "Failed",
    "msg_finished_successfully": "Finished Successfully",
    "btn_force_refresh": "Force Refresh",
    "lbl_gender": "Gender:",
    "glossary_manager": "Glossary Manager",
    "lbl_intensity": "Intensity:",
    "btn_link_to_speaker": "Link to Speaker",
    "msg_loading_qa": "Loading QA Report...",
    "btn_mark_approved": "Mark Approved",
    "btn_new_character": "New Character",
    "msg_no_qa_report": "No QA Report found.",
    "btn_open_configure": "Open / Configure",
    "btn_pause_queue": "Pause Queue",
    "btn_resume_queue": "Resume Queue",
    "btn_play_preview": "Play Preview",
    "lbl_provider": "Provider:",
    "status_queue_paused": "Queue Status: Paused",
    "status_queue_running": "Queue Status: Running",
    "btn_queue_for_processing": "Queue for Processing",
    "lbl_ready": "Ready",
    "desc_diagnostics": "Real-time view of registered AI Providers and their capability status.",
    "btn_remove_from_queue": "Remove from Queue (Dequeue)",
    "btn_render_all": "Render All",
    "btn_render_selected": "Render Selected",
    "btn_reset_to_auto": "Reset to Auto",
    "btn_resume_pipeline": "Resume Pipeline",
    "btn_save_all_changes": "Save All Changes",
    "lbl_search": "Search:",
    "placeholder_select_template": "Select a template",
    "lbl_source": "Source:",
    "lbl_target": "Target:",
    "btn_toggle_freeze": "Toggle Freeze",
    "desc_translation_memory": "Translation Memory (Auto-syncs with Review edits)",
    "btn_unpin_project": "Unpin Project",
    "window_tools": "Tools",
    "provider_diagnostics": "Provider Diagnostics",
    "qa_dashboard": "QA Dashboard",
    "template_browser": "Template & Workflow Browser",
    "translation_review": "Translation Review",
    "character_browser": "Character Browser",
    "voice_browser": "Voice Browser",
    "emotion_editor": "Emotion Editor"
}

# Translating to Vietnamese manually for the script
vi_translations = {
    "btn_apply_override": "Áp dụng Ghi đè",
    "btn_assign_selected": "Gán Lựa chọn",
    "assign_voice": "Gán Giọng đọc",
    "lbl_emotion": "Cảm xúc:",
    "msg_extracting_audio": "Đang tách âm thanh...",
    "msg_transcribing": "Đang nhận dạng lời nói...",
    "msg_translating": "Đang dịch...",
    "msg_synthesizing": "Đang tạo giọng AI...",
    "msg_stitching": "Đang ghép video cuối...",
    "msg_generating": "Đang tạo...",
    "msg_failed": "Thất bại",
    "msg_finished_successfully": "Hoàn thành Thành công",
    "btn_force_refresh": "Bắt buộc Làm mới",
    "lbl_gender": "Giới tính:",
    "glossary_manager": "Quản lý Thuật ngữ",
    "lbl_intensity": "Cường độ:",
    "btn_link_to_speaker": "Liên kết với Người nói",
    "msg_loading_qa": "Đang tải Báo cáo QA...",
    "btn_mark_approved": "Đánh dấu Đã duyệt",
    "btn_new_character": "Nhân vật mới",
    "msg_no_qa_report": "Không tìm thấy Báo cáo QA.",
    "btn_open_configure": "Mở / Cấu hình",
    "btn_pause_queue": "Tạm dừng Hàng đợi",
    "btn_resume_queue": "Tiếp tục Hàng đợi",
    "btn_play_preview": "Phát Nghe thử",
    "lbl_provider": "Nhà cung cấp:",
    "status_queue_paused": "Trạng thái Hàng đợi: Tạm dừng",
    "status_queue_running": "Trạng thái Hàng đợi: Đang chạy",
    "btn_queue_for_processing": "Đưa vào Hàng đợi Xử lý",
    "lbl_ready": "Sẵn sàng",
    "desc_diagnostics": "Xem thời gian thực các Nhà cung cấp AI đã đăng ký và trạng thái tính năng của họ.",
    "btn_remove_from_queue": "Xóa khỏi Hàng đợi",
    "btn_render_all": "Kết xuất Tất cả",
    "btn_render_selected": "Kết xuất Đã chọn",
    "btn_reset_to_auto": "Khôi phục Tự động",
    "btn_resume_pipeline": "Tiếp tục Quy trình",
    "btn_save_all_changes": "Lưu Tất cả Thay đổi",
    "lbl_search": "Tìm kiếm:",
    "placeholder_select_template": "Chọn một mẫu dự án",
    "lbl_source": "Gốc:",
    "lbl_target": "Đích:",
    "btn_toggle_freeze": "Bật/Tắt Đóng băng",
    "desc_translation_memory": "Bộ nhớ Dịch thuật (Tự động đồng bộ với Trình Đánh giá)",
    "btn_unpin_project": "Bỏ ghim Dự án",
    "window_tools": "Công cụ",
    "provider_diagnostics": "Chẩn đoán Nhà cung cấp",
    "qa_dashboard": "Bảng Điều khiển QA",
    "template_browser": "Trình duyệt Mẫu & Quy trình",
    "translation_review": "Đánh giá Bản dịch",
    "character_browser": "Trình duyệt Nhân vật",
    "voice_browser": "Trình duyệt Giọng đọc",
    "emotion_editor": "Trình chỉnh sửa Cảm xúc"
}

def update_json(file_path, base_dict, translations_dict=None):
    if not os.path.exists(file_path):
        data = {}
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
    for k, v in base_dict.items():
        if k not in data:
            if translations_dict and k in translations_dict:
                data[k] = translations_dict[k]
            else:
                data[k] = v
                
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

update_json('resources/i18n/en.json', new_keys)
update_json('resources/i18n/vi.json', new_keys, vi_translations)
print("Updated i18n JSON files successfully.")
