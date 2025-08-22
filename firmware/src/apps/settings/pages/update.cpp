#include "update.h"

UpdateSettingsPage::UpdateSettingsPage(lv_obj_t *parent) : BasePage(parent)
{
    // static lv_style_t *text_style = new lv_style_t;
    // lv_style_init(text_style);

    lv_obj_t *container = lv_obj_create(page);
    lv_obj_set_style_bg_opa(container, LV_OPA_0, 0);
    lv_obj_set_style_border_opa(container, LV_OPA_0, 0);
    lv_obj_center(container);

    lv_obj_set_flex_flow(container, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_flex_align(container, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
    lv_obj_set_style_pad_row(container, 6, 0);

    // lv_obj_add_style(container, text_style, 0);
    update_label = lv_label_create(container);
    lv_obj_set_style_text_font(update_label, &aktivgrotesk_regular_12pt_8bpp_subpixel, LV_PART_MAIN);
    lv_label_set_text(update_label, "SCAN TO UPDATE");

    update_qrcode = lv_qrcode_create(container, 80, LV_COLOR_MAKE(0x00, 0x00, 0x00), LV_COLOR_MAKE(0xFF, 0xFF, 0xFF));
    lv_qrcode_update(update_qrcode, "http://192.168.4.1/update", strlen("http://192.168.4.1/update"));
    lv_obj_align(update_qrcode, LV_ALIGN_CENTER, 0, -20);

    update_url_label = lv_label_create(container);
    lv_obj_set_style_text_font(update_url_label, &aktivgrotesk_regular_12pt_8bpp_subpixel, LV_PART_MAIN);
    lv_label_set_text(update_url_label, "192.168.4.1/update");
}

void UpdateSettingsPage::updateFromSystem(AppState state)
{
    // Network functionality removed - serial-only mode
    lv_label_set_text(update_label, "Serial Update Only");
    lv_obj_add_flag(update_qrcode, LV_OBJ_FLAG_HIDDEN);
    lv_obj_add_flag(update_url_label, LV_OBJ_FLAG_HIDDEN);
}
