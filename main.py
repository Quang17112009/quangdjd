from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os # Import os để đọc biến môi trường
import datetime
import time
import re
import random
import string
import threading
import requests
import telebot
from telebot import types

# --- CẤU HÌNH BOT ---
# LẤY API TOKEN TỪ BIẾN MÔI TRƯỜNG HOẶC ĐẶT TRỰC TIẾP
# Nếu chạy trên Render, nên dùng biến môi trường. Nếu chạy cục bộ, có thể đặt trực tiếp.
# ĐẢM BẢO TOKEN ĐƯỢC BAO BỌC BỞI DẤU NHÁY ĐƠN HOẶC KÉP VÀ ĐÚNG TOÀN BỘ
API_TOKEN = os.getenv('7983424898:AAGjKmtUBCL5H-ecT9F3_631xLJT_J7eS_c', '7983424898:AAGjKmtUBCL5H-ecT9F3_631xLJT_J7eS_c') # <<< THAY TOKEN THỰC CỦA BẠN VÀO ĐÂY VÀ ĐẢM BẢO NÓ ĐỦ DÀI VÀ CÓ DẤU KẾT THÚC >>>
bot = telebot.TeleBot(API_TOKEN)

# LẤY ADMIN ID TỪ BIẾN MÔI TRƯỜNG HOẶC ĐẶT TRỰC TIẾP
# Nếu có nhiều admin, biến môi trường có thể là chuỗi 'id1,id2,id3'
ADMIN_ID_STR = os.getenv('ADMIN_ID', '6915752059') # <<< THAY ID ADMIN CỦA BẠN VÀO ĐÂY, HOẶC NHIỀU ID CÁCH NHAU BẰNG DẤU PHẨY >>>
ADMIN_ID = [int(x.strip()) for x in ADMIN_ID_STR.split(',') if x.strip()]

# Cấu hình đường dẫn file
# Nếu dùng Render Volumes, bạn sẽ muốn thay đổi thành /data/wfkey.txt, /data/lsa.txt, v.v.
# Ví dụ: WFKEY_FILE = "/data/wfkey.txt"
WFKEY_FILE = "wfkey.txt"
LSA_FILE = "lsa.txt"
LSU_FILE = "lsu.txt"

# Lấy ngày tháng năm hiện tại
now = datetime.datetime.now()
ngay = now.day
thang = now.month
nam = now.year

# --- CÁC HÀM XỬ LÝ FILE ---
def read_wfkey_data():
    """Đọc dữ liệu key từ file wfkey.txt."""
    data = {}
    try:
        with open(WFKEY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = [p.strip() for p in line.strip().split(" | ")]
                if len(parts) >= 5: # Đảm bảo có đủ 5 phần cơ bản
                    key = parts[0]
                    hsd = parts[1]
                    hwid = parts[2]
                    status = parts[3]
                    lock_status = parts[4]
                    uids_str = parts[5] if len(parts) > 5 else '' # Lấy UIDs nếu có
                    uids = [u.strip() for u in uids_str.split(",")] if uids_str else []
                    data[key] = {
                        "hsd": hsd,
                        "hwid": hwid,
                        "status": status,
                        "lock_status": lock_status,
                        "uids": uids
                    }
    except FileNotFoundError:
        # Tạo file nếu chưa tồn tại
        with open(WFKEY_FILE, "w", encoding="utf-8") as f:
            pass # Chỉ tạo file rỗng
    return data

def write_wfkey_data(data):
    """Ghi dữ liệu key vào file wfkey.txt."""
    with open(WFKEY_FILE, "w", encoding="utf-8") as f:
        for key, value in data.items():
            uids_str = ",".join(value["uids"])
            f.write(f"{key} | {value['hsd']} | {value['hwid']} | {value['status']} | {value['lock_status']} | {uids_str}\n")

def log_admin_action(action_description):
    """Ghi log hành động của admin vào file lsa.txt."""
    now = datetime.datetime.now()
    timestamp = now.strftime("[%H:%M:%S %d/%m]")
    with open(LSA_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {action_description}\n")

def log_user_action(action_description):
    """Ghi log hành động của người dùng vào file lsu.txt."""
    now = datetime.datetime.now()
    timestamp = now.strftime("[%H:%M:%S %d/%m]")
    with open(LSU_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {action_description}\n")

def get_name_from_uid(uid):
    """
    Hàm giả định để lấy tên người dùng từ UID.
    Trong thực tế, bạn cần lưu tên người dùng khi họ tương tác với bot.
    """
    # Đây chỉ là một hàm giả định, trong thực tế bạn cần lưu tên người dùng
    # vào một cơ sở dữ liệu hoặc từ các tin nhắn trước đó của họ.
    return f"User_{uid}"

def generate_random_key():
    """Tạo một key ngẫu nhiên."""
    random_digits = ''.join(random.choices(string.digits, k=8))
    return f"ZzzRandom_Alpha{random_digits}"

# --- CÁC LỆNH CƠ BẢN ---
@bot.message_handler(commands=['start'])
def _(message):
    name = message.from_user.first_name or "bạn"
    user_id = message.from_user.id

    caption = (
        f'🤖 <b>Xin Chào Bạn <a href="tg://user?id={user_id}">{name}</a>!</b>\n\n'
        '<blockquote>Tôi Là Dự ĐoánXocdia88! Tôi Là Trợ Lý Alpha Được Tạo Bởi Một Thế Lực Wicked Đằng Sau Nó '
        'Và Tạo Bởi Các Người Đẹp Trai Nhất Thế Giới Giúp Bạn Kéo Về Nhà Sau 1 Tiếng Bế Bot. Chúng Tôi Hỗ Trợ Được Rất Nhiều Sàn. '
        'Dự ĐoánXocdia88 Cập Nhật Liên Tục Nên Bạn Có Thể Yên Tâm, Giá Lại Rất Hạt Dẻ</blockquote>\n\n'
        '<b>🐔 Hãy Sử Dụng Lệnh /whelp Để Có Một Trải Nghiệm Tuyệt Vời</b>'
    )

    # Đảm bảo link này còn hoạt động hoặc thay bằng link video của bạn
    video_url = "https://files.catbox.moe/qd4ypc.mp4"
    bot.send_video(
        chat_id=message.chat.id,
        video=video_url,
        caption=caption,
        parse_mode='HTML'
    )

@bot.message_handler(commands=['wkey'])
def handle_wkey(message):
    if message.chat.type != "private":
        bot.send_message(
            message.chat.id,
            "⚠️ <b>Vui Lòng Nhắn Tin Riêng Với Bot Để Sử Dụng Lệnh Này</b>",
            parse_mode='HTML'
        )
        return

    args = message.text.strip().split()
    uid = str(message.from_user.id)
    data = read_wfkey_data()

    user_key = None
    for k, v in data.items():
        if uid in v["uids"]:
            user_key = k
            break

    if len(args) == 1: # Chỉ nhập /wkey
        if not user_key:
            bot.reply_to(message, "Vui Lòng Nhập `/wkey + [Key]` để kích hoạt hoặc đăng nhập key.", parse_mode="Markdown")
            return

        key_data = data[user_key]

        # Kiểm tra HSD
        try:
            hsd_date_obj = datetime.datetime.strptime(key_data["hsd"], "%m-%d-%Y").date() # Sửa định dạng HSD nếu cần
            if hsd_date_obj < datetime.date.today():
                key_data["uids"] = [] # Xóa UID nếu hết hạn
                key_data["status"] = "Hết hạn" # Cập nhật trạng thái
                write_wfkey_data(data)
                bot.reply_to(message, "Key Này Đã Hết Hạn Vui Lòng Liên Hệ Admin Để Gia Hạn Thêm.")
                return
        except ValueError:
            if key_data["hsd"] == "Chưa kích hoạt":
                pass
            else:
                bot.reply_to(message, "Lỗi định dạng hạn sử dụng của key. Vui lòng liên hệ Admin.")
                return

        if key_data["lock_status"].lower() == "lock":
            bot.reply_to(message, "Key Đã Bị Ban Vui Lòng Liên Hệ Admin Để Biết Thêm Chi Tiết.")
            return

        send_key_info(message.chat.id, user_key, key_data, True)
        return

    elif len(args) == 2: # Nhập /wkey [Key]
        key_input = args[1]
        if key_input not in data:
            bot.reply_to(message, "Key Không Tồn Tại Liên Hệ Admin Để Mua.")
            return

        key_data = data[key_input]

        # Kiểm tra HSD của key mới nhập
        try:
            hsd_date_obj = datetime.datetime.strptime(key_data["hsd"], "%m-%d-%Y").date() # Sửa định dạng HSD nếu cần
            if hsd_date_obj < datetime.date.today():
                key_data["uids"] = []
                key_data["status"] = "Hết hạn"
                write_wfkey_data(data)
                bot.reply_to(message, "Key Này Đã Hết Hạn Vui Lòng Liên Hệ Admin Để Gia Hạn Thêm.")
                return
        except ValueError:
            if key_data["hsd"] != "Chưa kích hoạt":
                bot.reply_to(message, "Lỗi định dạng hạn sử dụng của key. Vui lòng liên hệ Admin.")
                return

        if key_data["lock_status"].lower() == "lock":
            bot.reply_to(message, "Key Đã Bị Ban Vui Lòng Liên Hệ Admin Để Biết Thêm Chi Tiết.")
            return

        # Nếu người dùng đã có key khác và muốn đổi sang key mới
        if user_key and user_key != key_input:
            old_key_data = data[user_key]
            if uid in old_key_data["uids"]:
                old_key_data["uids"].remove(uid)
            write_wfkey_data(data)
            bot.send_message(message.chat.id, f"Bạn đã đăng xuất khỏi key cũ: `{user_key}`", parse_mode="Markdown")

        # Thêm UID vào key mới
        if uid not in key_data["uids"]:
            if key_data["hwid"] != '0':
                try:
                    current_hwid_count = len(key_data["uids"])
                    max_hwid_allowed = int(key_data["hwid"])
                    if current_hwid_count >= max_hwid_allowed:
                        bot.reply_to(message, f"🤖 Key `{key_input}` Đã Đầy Thiết Bị ({current_hwid_count}/{max_hwid_allowed} thiết bị đã sử dụng).")
                        return
                except ValueError:
                    bot.reply_to(message, "Lỗi cấu hình HWID của key. Vui lòng liên hệ Admin.")
                    return

            key_data["uids"].append(uid)
            key_data["status"] = "Đã kích hoạt"
            if key_data["hsd"] == "Chưa kích hoạt":
                key_data["hsd"] = datetime.datetime.now().strftime("%m-%d-%Y") # HSD sẽ là ngày kích hoạt
            write_wfkey_data(data)
            log_user_action(f"UID {uid} kích hoạt/đăng nhập key {key_input}")

        send_key_info(message.chat.id, key_input, key_data, True)
        return

    else:
        bot.reply_to(message, "Sai cú pháp! Vui lòng nhập `/wkey` hoặc `/wkey [Key]`", parse_mode="Markdown")

def send_key_info(chat_id, key, key_data, show_logout=False):
    """Gửi thông tin key đến người dùng."""
    status_display = key_data['status']
    ban_display = ('Đã Bị Ban' if key_data['lock_status'].lower() == 'lock' else 'Chưa Bị Ban')

    msg = (
        "┌─┤Thông Tin WanKey├──⭓\n"
        f"├Key : <tg-spoiler>{key}</tg-spoiler>\n"
        f"├Hwid Devices: {key_data['hwid']}\n"
        f"├Expire Date : {key_data['hsd']}\n"
        f"├Status : {status_display}\n"
        f"├Ban : {ban_display}\n"
        "└───────────────⭓"
    )
    if show_logout:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Đăng Xuất", callback_data=f"logout_{key}"))
        bot.send_message(chat_id, msg, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(chat_id, msg, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("logout_"))
def handle_logout(call):
    """Xử lý yêu cầu đăng xuất key."""
    key = call.data.split("_", 1)[1]
    uid = str(call.from_user.id)
    data = read_wfkey_data()

    if key in data and uid in data[key]["uids"]:
        data[key]["uids"].remove(uid)
        write_wfkey_data(data)
        bot.answer_callback_query(call.id, "Đăng xuất thành công!")
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except telebot.apihelper.ApiTelegramException as e:
            if "message is not modified" not in str(e):
                print(f"Lỗi khi xóa markup: {e}")
        bot.send_message(call.message.chat.id, f"Bạn đã đăng xuất khỏi key `{key}`", parse_mode="Markdown")
        log_user_action(f"UID {uid} đăng xuất khỏi key {key}")
    else:
        bot.answer_callback_query(call.id, "Không thể đăng xuất hoặc bạn không sở hữu key này.")

@bot.message_handler(commands=['whelp'])
def send_help(message):
    now = datetime.datetime.now()
    thu = ['Hai', 'Ba', 'Tư', 'Năm', 'Sáu', 'Bảy', 'Chủ Nhật'][now.weekday()]
    ngay = now.day
    thang = now.month
    nam = now.year

    user_id = message.from_user.id
    user_name = message.from_user.first_name

    text = f"""
<b>Xin chào bạn <a href="tg://user?id={user_id}">{user_name}</a>, tôi là Dự ĐoánXocdia88 - Tập đoàn của Wicked</b>

📆 Hôm nay là: Th.{thu} {ngay}/{thang}/{nam}
🆔 ID của bạn <a href="tg://user?id={user_id}">{user_name}</a>: <code>{user_id}</code>

<blockquote>
» /wfox + Dự đoán T/X theo cầu 70-80
» /wkey + [Nhập/Login Key để sử dụng]
» /giakey + [Xem bảng giá Key]
» /admin + [Chi tiết Admin]
» /ls + [Xem lịch sử Admin/User]
» /akey + [Admin menu tạo Key]
» /ekey [Key] + [Admin edit Key]
</blockquote>

📬 <b>Hãy sử dụng dịch vụ của Dự ĐoánXocdia88, sẽ không làm bạn thất vọng!</b>
"""
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['giakey'])
def gia(message):
    try:
        waiting_msg = bot.send_message(
            message.chat.id,
            "<b>Hãy Đợi Một Chút Nhé Chúng Tôi Không Để Bạn Chờ Lâu</b> ...",
            parse_mode="HTML"
        )

        response = requests.get("https://api.ffcommunity.site/randomvideo.php") # Đảm bảo link này còn hoạt động
        data_api = response.json()
        video_url = data_api['url']

        caption = (
            "🔎 <b>Hãy Xem Seller Dưới Đây Phù Hợp Vui Túi Tiền Của Mình Nhé</b>\n\n"
            "<blockquote>┌ SELLER WKEY Dự ĐoánXocdia88\n"
            "├ 1 NGÀY : 20K\n"
            "├ 1 TUẦN : 50K\n"
            "├ 1 THÁNG : 150K\n"
            "├ 6 THÁNG : 350K\n"
            "├ VĨNH VIỄN : 600K\n"
            "└────────────</blockquote>\n\n"
            "🚫 <b>Lưu Ý : Vui Lòng Mua Ở Các Admin Dự ĐoánXocdia88 Alpha Không Nên Mua Ở Người Khác Mất Tiền Tự Chịu</b>"
        )

        bot.send_video(
            message.chat.id,
            video_url,
            caption=caption,
            parse_mode="HTML",
        )

        bot.delete_message(chat_id=message.chat.id, message_id=waiting_msg.message_id)

    except Exception as e:
        bot.send_message(message.chat.id, f"😥 Oops! Hãy Chạy Lại Lệnh /giakey Lỗi: `{e}`", parse_mode="Markdown")
        log_user_action(f"UID {message.from_user.id} gặp lỗi khi dùng /giakey: {e}")

@bot.message_handler(commands=['wfox'])
def wfox_dudoan(message):
    if message.chat.type != "private":
        bot.send_message(
            message.chat.id,
            "⚠️ <b>Vui Lòng Nhắn Tin Riêng Với Bot Để Sử Dụng Lệnh Này</b>",
            parse_mode='HTML'
        )
        return

    user_id = str(message.from_user.id)
    wfkey_data = read_wfkey_data()

    user_key = None
    for key, value in wfkey_data.items():
        if user_id in value.get("uids", []):
            user_key = key
            break

    if user_key is None:
        bot.send_message(
            message.chat.id,
            "<b>Bạn Chưa Có Key!</b> Vui lòng mua key hoặc tham gia các event để nhận key miễn phí.",
            parse_mode='HTML'
        )
    else:
        key_info = wfkey_data[user_key]

        if key_info.get("lock_status") == "lock":
            bot.send_message(
                message.chat.id,
                "<b>Key của bạn đã bị ban!</b> Vui lòng liên hệ Admin để biết thêm chi tiết.",
                parse_mode='HTML'
            )
            return

        try:
            hsd_date = datetime.datetime.strptime(key_info["hsd"], "%m-%d-%Y").date() # Sửa định dạng HSD nếu cần
            if hsd_date < datetime.date.today():
                key_info["uids"] = []
                key_info["status"] = "Hết hạn"
                write_wfkey_data(wfkey_data)
                bot.send_message(
                    message.chat.id,
                    "<b>Key của bạn đã hết hạn!</b> Vui lòng gia hạn hoặc mua key mới.",
                    parse_mode='HTML'
                )
            else:
                markup = types.InlineKeyboardMarkup()
                xocdia_button = types.InlineKeyboardButton("XocDia88", callback_data="xocdia88")
                sumclub_button = types.InlineKeyboardButton("SumClub", callback_data="sumclub")
                markup.add(xocdia_button, sumclub_button)

                bot.send_message(
                    message.chat.id,
                    f"<b>🎃 Xin Chào Đại Gia {message.from_user.first_name}! Dự ĐoánXocdia88 Được Cập Nhật Thường Xuyên Nên Quý Khách Yên Tâm Sử Dụng </b>\n\n"
                    "<blockquote>🔇 Lưu Ý : Dự ĐoánXocdia88 Chỉ Hỗ Trợ 2 Sàn Casino XocDia88 Và SumClub Để Có Một Trải Nghiệm Tuyệt Vời Cho Đại Gia Chúng Tôi Không Đảm Bảo Kết Quả Đến 100% Nhưng Chúng Tôi Đảm Bảo Kết Quả Thật Từ 70-80% Và Thuật Toán Chuyên Dự Đoán Phiên Đến 1000 Phiên Và Tâm Huyết Nên Quý Khách Tâm Huyết 🎰</blockquote>\n\n"
                    "<b>🀄 Vui Lòng Chọn Sàn Bạn Muốn Chơi Bằng Cách Nhấn Button Bên Dưới :</b>",
                    parse_mode='HTML',
                    reply_markup=markup
                )
        except ValueError:
            bot.send_message(
                message.chat.id,
                "<b>Lỗi định dạng hạn sử dụng key.</b> Vui lòng liên hệ Admin.",
                parse_mode='HTML'
            )


@bot.callback_query_handler(func=lambda call: call.data == 'xocdia88')
def handle_xocdia88(call):
    try:
        url = "https://taixiu.system32-cloudfare-356783752985678522.monster/api/luckydice/GetSoiCau?access_token="

        res = requests.get(url)
        if res.status_code != 200:
            raise Exception(f"API lỗi: {res.status_code}")

        data = res.json()
        if not isinstance(data, list) or not data:
            raise Exception("Không có dữ liệu từ API hoặc định dạng không đúng.")

        lst = data[:10]
        chuoi = ""
        tong_all = 0
        so_5_6 = 0
        xu_huong = []
        # du_doan_truoc = "" # Biến này không được sử dụng
        # thang = 0 # Biến này không được sử dụng
        # thua = 0 # Biến này không được sử dụng
        reclycle_diff = []
        list_ketqua = []
        xu_huong_seq = []

        for i in lst:
            dice_sum = i["DiceSum"]
            tong_all += dice_sum
            ket_qua = "X" if dice_sum <= 10 else "T"
            chuoi += ket_qua
            list_ketqua.append(ket_qua)

            if len(xu_huong) > 0:
                xu_huong.append(dice_sum - xu_huong[-1])
                reclycle_diff.append(abs(dice_sum - xu_huong[-1]))
            else:
                xu_huong.append(dice_sum)

            if len(xu_huong) >= 3:
                xu_huong_seq.append(tuple(xu_huong[-3:]))

        trung_binh = tong_all / 10
        du_doan = "T" if trung_binh > 10.5 else "X"

        tang = sum(1 for i in xu_huong[1:] if i > 0)
        giam = sum(1 for i in xu_huong[1:] if i < 0)

        ti_le_5_6 = so_5_6 / 30 # so_5_6 luôn bằng 0, nên ti_le_5_6 luôn bằng 0

        dao_dong = sum(1 for i in reclycle_diff if i >= 2)
        reclycle_score = 1 if dao_dong <= 3 else 0

        last_dice_sum = data[0]["DiceSum"]
        bliplack_score = 1 if last_dice_sum in [5, 7, 13, 11] or (str(last_dice_sum) and str(last_dice_sum)[0] == str(last_dice_sum)[-1]) else 0

        count_1 = sum(i["FirstDice"] == 1 or i["SecondDice"] == 1 or i["ThirdDice"] == 1 for i in lst)
        count_3 = sum(i["FirstDice"] == 3 or i["SecondDice"] == 3 or i["ThirdDice"] == 3 for i in lst)
        dicerefund_score = 1 if (count_1 + count_3) >= 9 else 0

        count_t = list_ketqua.count("T")
        count_x = list_ketqua.count("X")
        becau_score = 1 if abs(count_t - count_x) <= 2 else 0

        score = 0
        if trung_binh > 10.5:
            score += 1
        if tang > giam:
            score += 1
        if ti_le_5_6 > 0.4:
            score += 1
        score += reclycle_score + bliplack_score + dicerefund_score + becau_score

        raw_score = int((score / 7) * 100)
        ti_le = max(60, min(raw_score, 90))

        ti_le_text = ""
        if ti_le >= 80:
            ti_le_text = f"{ti_le}% - Cược Lớn Auto Húp All-in Luôn"
        elif ti_le >= 70:
            ti_le_text = f"{ti_le}% - Cược Vừa Để Mất Tránh Tiêc "
        else:
            ti_le_text = f"{ti_le}% - Cược Nhẹ Làm Nhử "

        theo_cau = du_doan

        if xu_huong_seq:
            last_seq = xu_huong_seq[-1]
            if last_seq == (2, 1, 2):
                theo_cau = "X"
            elif last_seq == (1, 2, 3):
                theo_cau = "T"
            elif last_seq == (3, 2, 1):
                theo_cau = "X"

        if 11 <= last_dice_sum <= 13:
            theo_cau = "X"

        phien = int(data[0]["SessionId"]) + 1

        nd = f"""
<b>🔇 Xin Chào Người Đẹp ! Hãy Làm Vài Tay Để Dự ĐoánXocdia88 Alpha Kéo Bạn Về Bờ Hãy Làm Vài Tay Nào !</b>

<blockquote>🔎<b> Phân Tích Phiên #<b>{phien}</b></b>

📭 10 Phiên Gần Nhất: <b>{chuoi}</b>

🔖 Dự Đoán: <b>{theo_cau}</b>

📊 Tỷ Lệ: {ti_le_text}</blockquote>

<b>[ T ] là Tài, [ X ] là Xỉu Nên Lưu Ý Chọn Đúng Cược Nhen</b>
"""
        web_app_url = 'https://play.xocdia88.it.com' # Đảm bảo link này còn hoạt động

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text='XocDia 88', url=web_app_url))
        markup.add(types.InlineKeyboardButton(text='🔄 Reload', callback_data='xocdia88'))

        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=nd,
                parse_mode="HTML",
                reply_markup=markup
            )
        except telebot.apihelper.ApiTelegramException as e:
            if "message is not modified" not in str(e):
                raise e

    except Exception as e:
        import traceback
        traceback.print_exc()
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Lỗi khi lấy dự đoán XocDia88: `{str(e)}`",
            parse_mode="Markdown"
        )
        log_user_action(f"UID {call.from_user.id} gặp lỗi khi dùng XocDia88: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'sumclub')
def handle_sumclub(call):
    bot.answer_callback_query(call.id, "Chức năng này chưa được cập nhật!")
    bot.send_message(call.message.chat.id, "Chưa Cập Nhật Sàn *SumClub*!", parse_mode="Markdown")

# --- CÁC LỆNH ADMIN ---
@bot.message_handler(commands=['admin'], func=lambda message: message.from_user.id in ADMIN_ID)
def handle_admin(message):
    # Bạn có thể thêm các thông tin hoặc menu admin ở đây
    bot.send_message(message.chat.id, "Chào Admin! Đây là khu vực quản lý.")
    # Có thể thêm các nút bấm hoặc hướng dẫn sử dụng các lệnh admin khác ở đây.

@bot.message_handler(commands=['akey'], func=lambda message: message.from_user.id in ADMIN_ID)
def handle_akey_menu(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Tạo Random Key", callback_data="akey_random"),
               types.InlineKeyboardButton("Tạo Key Tùy Chỉnh", callback_data="akey_custom"))
    bot.send_message(message.chat.id, "Chọn cách tạo key:", reply_markup=markup)

@bot.message_handler(commands=['taokey'], func=lambda message: message.from_user.id in ADMIN_ID)
def handle_taokey_command(message):
    bot.send_message(
        message.chat.id,
        "Vui lòng nhập thông tin key theo định dạng: `Tên Key | Số Ngày HSD | Số HWID (0 nếu không giới hạn)`\n"
        "Ví dụ: `VIPGoldKey | 30 | 1`",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(message, process_taokey_input)

def process_taokey_input(message):
    try:
        parts = [p.strip() for p in message.text.split('|')]
        if len(parts) != 3:
            raise ValueError("Định dạng không đúng. Vui lòng nhập: `Tên Key | Số Ngày HSD | Số HWID`")

        new_key = parts[0]
        hsd_days = int(parts[1])
        hwid_limit = parts[2]

        if not new_key:
            raise ValueError("Tên key không được để trống.")
        if not hwid_limit.strip():
            hwid_limit = "0"

        expiry_date = datetime.date.today() + datetime.timedelta(days=hsd_days)
        hsd_calculated = expiry_date.strftime("%m-%d-%Y") # Định dạng HSD

        data = read_wfkey_data()
        if new_key in data:
            bot.send_message(message.chat.id, f"Key `{new_key}` đã tồn tại. Vui lòng chọn tên khác.", parse_mode="Markdown")
            return

        data[new_key] = {
            "hsd": hsd_calculated,
            "hwid": hwid_limit,
            "status": "Chưa kích hoạt",
            "lock_status": "unlock",
            "uids": []
        }
        write_wfkey_data(data)

        response_text = (
            f"✅ Đã tạo key thành công!\n"
            f"<b>Key:</b> <tg-spoiler>{new_key}</tg-spoiler>\n"
            f"<b>Hạn sử dụng:</b> {hsd_calculated}\n"
            f"<b>Giới hạn HWID:</b> {hwid_limit}"
        )
        bot.send_message(message.chat.id, response_text, parse_mode="HTML")
        log_admin_action(f"[CREATE] Admin {message.from_user.id} đã tạo key: {new_key} | HSD: {hsd_calculated} | HWID: {hwid_limit}")

    except ValueError as e:
        bot.send_message(message.chat.id, f"Lỗi: {e}\nVui lòng nhập đúng định dạng: `Tên Key | Số Ngày HSD | Số HWID`", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"Đã xảy ra lỗi không mong muốn: `{e}`", parse_mode="Markdown")
        log_admin_action(f"[ERROR] Lỗi khi tạo key bởi admin {message.from_user.id}: {e}")

@bot.message_handler(commands=['ekey'], func=lambda message: message.from_user.id in ADMIN_ID)
def handle_ekey(message):
    try:
        key_to_edit = message.text.split(" ", 1)[1].strip()
        data = read_wfkey_data()

        if key_to_edit not in data:
            bot.send_message(message.chat.id, f"Không tìm thấy **Key**: `{key_to_edit}`", parse_mode="Markdown")
            return

        key_info = data[key_to_edit]

        used_hwid_count = len(key_info['uids'])
        max_hwid_limit = key_info['hwid']
        hwid_display = f"{used_hwid_count}/{max_hwid_limit}" if max_hwid_limit != '0' else "Không giới hạn"

        response_text = (
            f"<blockquote>┌───────────\n"
            f"├─ Key : <tg-spoiler>{key_to_edit}</tg-spoiler>\n"
            f"├─ HWID Devices: {hwid_display}\n"
            f"├─ Kích Hoạt : {key_info['status']}\n"
            f"├─ Ban : {key_info['lock_status']}\n"
            f"├─ HSD : {key_info['hsd']}\n"
            f"└───────────</blockquote>\n\n"
            f"🤖 Pixel quảng cáo nè: Hãy mua VIP để sử dụng ngon hơn nhé :>"
        )

        markup = types.InlineKeyboardMarkup(row_width=2)
        lock_btn_text = "UnBan" if key_info['lock_status'] == "lock" else "Ban"

        markup.add(
            types.InlineKeyboardButton("Edit Expire", callback_data=f"ekey_edit_exp_{key_to_edit}"),
            types.InlineKeyboardButton(lock_btn_text, callback_data=f"ekey_toggle_ban_{key_to_edit}")
        )
        markup.add(
            types.InlineKeyboardButton("Quản lý HWID", callback_data=f"ekey_hwid_list_{key_to_edit}"),
            types.InlineKeyboardButton("Del Key", callback_data=f"ekey_del_key_{key_to_edit}")
        )

        bot.send_message(message.chat.id, response_text, reply_markup=markup, parse_mode="HTML")

    except IndexError:
        bot.send_message(message.chat.id, "Vui lòng nhập Key theo định dạng: `/ekey [Key]`", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.from_user.id in ADMIN_ID and call.data.startswith(("akey_", "ekey_", "ls_")))
def callback_query_admin(call):
    parts = call.data.split("_")
    action_group = parts[0] + "_" + parts[1]
    key = parts[-1] if len(parts) > 2 else None
    data = read_wfkey_data()

    if action_group == "ekey_edit_exp":
        bot.send_message(call.message.chat.id, "Vui lòng Nhập Hạn Sử Dụng Muốn Trừ Hoặc Cộng (Ví Dụ: Nếu Trừ Thì `-1`, Còn Cộng Thì `1`). **Định dạng HSD sẽ là MM-DD-YYYY.**", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, lambda m: _ekey_edit_expire_input(m, key))

    elif action_group == "ekey_toggle_ban":
        if key in data:
            new_status = "unlock" if data[key]["lock_status"] == "lock" else "lock"
            data[key]["lock_status"] = new_status
            status_text_log = "UNBAN" if new_status == "unlock" else "BAN"
            status_text_display = "UnBan" if new_status == "unlock" else "Ban"

            if new_status == "lock":
                data[key]["status"] = "Đã bị ban"
            elif new_status == "unlock" and data[key]["hsd"] != "Chưa kích hoạt":
                # Chỉ đặt lại status nếu key không hết hạn và được unban
                try:
                    hsd_date_obj = datetime.datetime.strptime(data[key]["hsd"], "%m-%d-%Y").date()
                    if hsd_date_obj >= datetime.date.today():
                        data[key]["status"] = "Đã kích hoạt"
                    else:
                        data[key]["status"] = "Hết hạn" # Vẫn hết hạn nếu HSD đã qua
                except ValueError:
                    data[key]["status"] = "Lỗi HSD" # Xử lý nếu HSD định dạng sai
            
            write_wfkey_data(data)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f"Đã **{status_text_display}** Key `{key}`", parse_mode="Markdown")
            log_admin_action(f"[{status_text_log}] Admin {call.from_user.id} đã {status_text_display} Key {key}")

    elif action_group == "ekey_hwid_list":
        if key in data:
            uids = data[key]["uids"]
            hwid_list_text = f"**Danh Sách HWID Cho Key** `{key}`:\n\n"
            if uids:
                for uid in uids:
                    hwid_list_text += f"<blockquote>UID: {uid} - Tên: {get_name_from_uid(uid)}</blockquote>\n"
            else:
                hwid_list_text += "Key này chưa có HWID nào."

            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("Xóa User từ HWID", callback_data=f"ekey_del_user_{key}"),
                types.InlineKeyboardButton("Thêm HWID", callback_data=f"ekey_add_hwid_{key}")
            )
            markup.add(types.InlineKeyboardButton("Giảm giới hạn HWID", callback_data=f"ekey_dec_hwid_limit_{key}"))
            markup.add(types.InlineKeyboardButton("Tăng giới hạn HWID", callback_data=f"ekey_inc_hwid_limit_{key}"))

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=hwid_list_text, reply_markup=markup, parse_mode="HTML")

    elif action_group == "ekey_del_key":
        if key in data:
            del data[key]
            write_wfkey_data(data)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f"Đã **Xóa Key** `{key}`", parse_mode="Markdown")
            log_admin_action(f"[DEL] Admin {call.from_user.id} đã Xóa Key {key}")

    elif action_group == "ekey_del_user":
        bot.send_message(call.message.chat.id, "Vui Lòng Nhập **UID** Muốn Xóa Khỏi Key:", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, lambda m: _ekey_del_user_input(m, key))

    elif action_group == "ekey_add_hwid":
        bot.send_message(call.message.chat.id, "Vui Lòng Nhập **UID** Cần Thêm Vào Key (hoặc nhập '0' để đặt lại HWID về 0):", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, lambda m: _ekey_add_hwid_input(m, key))

    elif action_group == "ekey_dec_hwid": # Nút bấm này không có trong menu, nhưng logic vẫn được giữ
        bot.send_message(call.message.chat.id, "Vui lòng nhập **Số lượng HWID** muốn giảm (ví dụ: `-1` để giảm 1):", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, lambda m: _ekey_change_hwid_limit(m, key, 'decrease'))

    elif action_group == "ekey_inc_hwid": # Nút bấm này không có trong menu, nhưng logic vẫn được giữ
        bot.send_message(call.message.chat.id, "Vui lòng nhập **Số lượng HWID** muốn tăng (ví dụ: `1` để tăng 1):", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, lambda m: _ekey_change_hwid_limit(m, key, 'increase'))

    elif action_group == "akey_random":
        bot.send_message(call.message.chat.id, "Vui lòng nhập **Số Lượng Key** | **Số Ngày HSD** | **Số HWID (0 nếu không giới hạn)** (ví dụ: `5 | 30 | 1`)", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, process_random_key_input)

    elif action_group == "akey_custom":
        bot.send_message(call.message.chat.id, "Vui lòng nhập **Tên Key** | **Số Ngày HSD** | **Số HWID (0 nếu không giới hạn)** (ví dụ: `MyKey123 | 60 | 2`)", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, process_custom_key_input)

    elif action_group == "ls_admin":
        try:
            with open(LSA_FILE, "r", encoding="utf-8") as f:
                history_content = f.read()
            text_to_send = f"**Lịch Sử Admin**:\n\n`{history_content}`" if history_content else "Lịch Sử Admin trống."
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=text_to_send, parse_mode="Markdown")
        except FileNotFoundError:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f"File `{LSA_FILE}` không tồn tại.", parse_mode="Markdown")

    elif action_group == "ls_user":
        try:
            with open(LSU_FILE, "r", encoding="utf-8") as f:
                history_content = f.read()
            text_to_send = f"**Lịch Sử User**:\n\n`{history_content}`" if history_content else "Lịch Sử User trống."
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=text_to_send, parse_mode="Markdown")
        except FileNotFoundError:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f"File `{LSU_FILE}` không tồn tại.", parse_mode="Markdown")


@bot.message_handler(commands=['ls'], func=lambda message: message.from_user.id in ADMIN_ID)
def handle_ls(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Lịch Sử Admin", callback_data="ls_admin"),
               types.InlineKeyboardButton("Lịch Sử User", callback_data="ls_user"))
    bot.send_message(message.chat.id, "Chọn lịch sử muốn xem:", reply_markup=markup)

def _ekey_edit_expire_input(message, key):
    try:
        change_value = int(message.text.strip())
        data = read_wfkey_data()
        if key in data:
            current_hsd_str = data[key]["hsd"]
            if current_hsd_str == "Chưa kích hoạt":
                bot.send_message(message.chat.id, "Key này chưa được kích hoạt, không thể thay đổi HSD. HSD chỉ thay đổi khi Key được kích hoạt.", parse_mode="Markdown")
                return

            try:
                current_date = datetime.datetime.strptime(current_hsd_str, "%m-%d-%Y").date() # Định dạng HSD
                new_date = current_date + datetime.timedelta(days=change_value)
                data[key]["hsd"] = new_date.strftime("%m-%d-%Y") # Định dạng HSD
                write_wfkey_data(data)
                bot.send_message(message.chat.id, f"Đã cập nhật **HSD** cho Key `{key}` thành `{data[key]['hsd']}`", parse_mode="Markdown")
                log_admin_action(f"[EDIT EXP] Admin {message.from_user.id} đã thay đổi HSD Key {key} thêm {change_value} ngày. HSD mới: {data[key]['hsd']}")
            except ValueError:
                bot.send_message(message.chat.id, "Định dạng HSD trong file `wfkey.txt` không hợp lệ. Vui lòng sửa thủ công hoặc kiểm tra lại.", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"Không tìm thấy Key: `{key}`", parse_mode="Markdown")
    except ValueError:
        bot.send_message(message.chat.id, "Giá trị nhập vào không hợp lệ. Vui lòng nhập một số nguyên.", parse_mode="Markdown")

def _ekey_del_user_input(message, key):
    uid_to_delete = message.text.strip()
    data = read_wfkey_data()
    if key in data:
        if uid_to_delete in data[key]["uids"]:
            data[key]["uids"].remove(uid_to_delete)
            write_wfkey_data(data)
            bot.send_message(message.chat.id, f"Đã xóa **UID** `{uid_to_delete}` khỏi Key `{key}`.", parse_mode="Markdown")
            log_admin_action(f"[DEL USER] Admin {message.from_user.id} đã xóa UID {uid_to_delete} khỏi Key {key}")
        else:
            bot.send_message(message.chat.id, f"Không tìm thấy **UID** `{uid_to_delete}` trong Key `{key}`.", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"Không tìm thấy Key: `{key}`", parse_mode="Markdown")

def _ekey_add_hwid_input(message, key):
    uid_or_reset_hwid = message.text.strip()
    data = read_wfkey_data()

    if key not in data:
        bot.send_message(message.chat.id, f"Không tìm thấy Key: `{key}`", parse_mode="Markdown")
        return

    key_data = data[key]

    if uid_or_reset_hwid == '0':
        key_data["uids"] = []
        key_data["status"] = "Chưa kích hoạt"
        write_wfkey_data(data)
        bot.send_message(message.chat.id, f"Đã đặt lại tất cả HWID và trạng thái cho Key `{key}` về 'Chưa kích hoạt'.", parse_mode="Markdown")
        log_admin_action(f"[RESET HWID] Admin {message.from_user.id} đã đặt lại HWID cho Key {key}")
        return

    new_uid = uid_or_reset_hwid
    if new_uid in key_data["uids"]:
        bot.send_message(message.chat.id, f"**UID** `{new_uid}` đã tồn tại trong Key `{key}`.", parse_mode="Markdown")
        return

    if key_data["hwid"] != '0':
        try:
            current_hwid_count = len(key_data["uids"])
            max_hwid_limit = int(key_data["hwid"])
            if current_hwid_count >= max_hwid_limit:
                bot.send_message(message.chat.id, f"Key `{key}` đã đạt giới hạn HWID ({max_hwid_count}/{max_hwid_limit} thiết bị). Không thể thêm UID mới.", parse_mode="Markdown")
                return
        except ValueError:
            bot.send_message(message.chat.id, "Lỗi cấu hình HWID của key. Vui lòng liên hệ Admin.", parse_mode="Markdown")
            return

    key_data["uids"].append(new_uid)
    key_data["status"] = "Đã kích hoạt"

    if key_data["hsd"] == "Chưa kích hoạt":
        key_data["hsd"] = datetime.datetime.now().strftime("%m-%d-%Y") # Định dạng HSD
        bot.send_message(message.chat.id, f"Đã thêm **HWID** `{new_uid}` vào Key `{key}`. Key đã được kích hoạt và HSD được đặt là ngày hôm nay: `{key_data['hsd']}`.", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"Đã thêm **HWID** `{new_uid}` vào Key `{key}`.", parse_mode="Markdown")

    write_wfkey_data(data)
    log_admin_action(f"[ADD HWID] Admin {message.from_user.id} đã thêm HWID {new_uid} vào Key {key}. Key kích hoạt.")

def _ekey_change_hwid_limit(message, key, change_type):
    try:
        change_amount = int(message.text.strip())
        data = read_wfkey_data()

        if key not in data:
            bot.send_message(message.chat.id, f"Không tìm thấy Key: `{key}`", parse_mode="Markdown")
            return

        current_hwid_limit = int(data[key]["hwid"]) if data[key]["hwid"].isdigit() else 0

        if change_type == 'increase':
            new_hwid_limit = current_hwid_limit + change_amount
            action_text = "tăng"
        elif change_type == 'decrease':
            new_hwid_limit = current_hwid_limit - change_amount
            action_text = "giảm"
        else:
            bot.send_message(message.chat.id, "Lỗi nội bộ. Loại thay đổi HWID không hợp lệ.", parse_mode="Markdown")
            return

        if new_hwid_limit < 0:
            new_hwid_limit = 0

        data[key]["hwid"] = str(new_hwid_limit)
        write_wfkey_data(data)
        bot.send_message(message.chat.id, f"Đã {action_text} giới hạn **HWID** cho Key `{key}` thành `{new_hwid_limit}`.", parse_mode="Markdown")
        log_admin_action(f"[CHANGE HWID LIMIT] Admin {message.from_user.id} đã {action_text} giới hạn HWID của Key {key} thành {new_hwid_limit}")

    except ValueError:
        bot.send_message(message.chat.id, "Giá trị nhập vào không hợp lệ. Vui lòng nhập một số nguyên.", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"Đã xảy ra lỗi không mong muốn: `{e}`", parse_mode="Markdown")
        log_admin_action(f"[ERROR] Lỗi khi thay đổi giới hạn HWID bởi admin {message.from_user.id}: {e}")

def process_random_key_input(message):
    try:
        parts = [p.strip() for p in message.text.split('|')]
        if len(parts) != 3:
            raise ValueError("Định dạng không đúng. Vui lòng nhập: `Số Lượng | Số Ngày HSD | Số HWID`")

        num_keys = int(parts[0])
        hsd_days = int(parts[1])
        hwid_limit = parts[2]

        if not hwid_limit.strip():
            hwid_limit = "0"

        expiry_date = datetime.date.today() + datetime.timedelta(days=hsd_days)
        hsd_calculated = expiry_date.strftime("%m-%d-%Y") # Định dạng HSD

        generated_keys_info = []
        data = read_wfkey_data() # Đọc dữ liệu hiện có để kiểm tra trùng lặp
        
        for _ in range(num_keys):
            new_key = generate_random_key()
            while new_key in data: # Đảm bảo key không bị trùng
                new_key = generate_random_key()

            data[new_key] = {
                "hsd": hsd_calculated,
                "hwid": hwid_limit,
                "status": "Chưa kích hoạt",
                "lock_status": "unlock",
                "uids": []
            }
            generated_keys_info.append(f"<tg-spoiler>{new_key}</tg-spoiler> | HSD: {hsd_calculated} | HWID Limit: {hwid_limit}")

        write_wfkey_data(data) # Ghi tất cả key mới vào file

        response_text = "<b>Danh Sách Key Đã Random (Đã Lưu Vào File)</b>:\n\n" + "\n".join([f"<blockquote>{key_info}</blockquote>" for key_info in generated_keys_info])
        bot.send_message(message.chat.id, response_text, parse_mode="HTML")
        log_admin_action(f"[GENERATE RANDOM] Admin {message.from_user.id} đã tạo {num_keys} key ngẫu nhiên với HSD: {hsd_calculated}, HWID Limit: {hwid_limit}")

    except ValueError as e:
        bot.send_message(message.chat.id, f"Lỗi: {e}\nVui lòng nhập đúng định dạng: `Số Lượng | Số Ngày HSD | Số HWID` (ví dụ: `5 | 30 | 1`)", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"Đã xảy ra lỗi không mong muốn: `{e}`", parse_mode="Markdown")
        log_admin_action(f"[ERROR] Lỗi khi tạo random key bởi admin {message.from_user.id}: {e}")

def process_custom_key_input(message):
    try:
        parts = [p.strip() for p in message.text.split('|')]
        if len(parts) != 3:
            raise ValueError("Định dạng không đúng. Vui lòng nhập: `Tên Key | Số Ngày HSD | Số HWID`")

        new_key = parts[0]
        hsd_days = int(parts[1])
        hwid_limit = parts[2]

        if not new_key:
            raise ValueError("Tên key không được để trống.")
        if not hwid_limit.strip():
            hwid_limit = "0"

        expiry_date = datetime.date.today() + datetime.timedelta(days=hsd_days)
        hsd_calculated = expiry_date.strftime("%m-%d-%Y") # Định dạng HSD

        data = read_wfkey_data()
        if new_key in data:
            bot.send_message(message.chat.id, f"Key `{new_key}` đã tồn tại. Vui lòng chọn tên khác.", parse_mode="Markdown")
            return

        data[new_key] = {
            "hsd": hsd_calculated,
            "hwid": hwid_limit,
            "status": "Chưa kích hoạt",
            "lock_status": "unlock",
            "uids": []
        }
        write_wfkey_data(data)
        bot.send_message(message.chat.id, f"Đã tạo **Key** `{new_key}` với HSD: `{hsd_calculated}` và HWID Limit: `{hwid_limit}`.", parse_mode="Markdown")
        log_admin_action(f"[CREATE CUSTOM] Admin {message.from_user.id} đã tạo Key {new_key} với HSD: {hsd_calculated}, HWID Limit: {hwid_limit}")

    except ValueError as e:
        bot.send_message(message.chat.id, f"Lỗi: {e}\nVui lòng nhập đúng định dạng: `Tên Key | Số Ngày HSD | Số HWID` (ví dụ: `MyKey123 | 60 | 2`)", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"Đã xảy ra lỗi không mong muốn: `{e}`", parse_mode="Markdown")
        log_admin_action(f"[ERROR] Lỗi khi tạo custom key bởi admin {message.from_user.id}: {e}")

# --- KHỞI CHẠY BOT ---
def get_bot_info():
    try:
        me = bot.get_me()
        print(f"NAME BOT : {me.first_name}")
        print(f"Username : @{me.username}")
    except Exception as e:
        print("Lỗi khi lấy thông tin bot:", e)

def polling_with_retry():
    while True:
        try:
            print("Bắt đầu polling bot...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print("Lỗi khi polling:", e)
            print("Đang thử lại sau 5 giây...")
            time.sleep(5)

if __name__ == "__main__":
    # Đảm bảo các file dữ liệu tồn tại
    read_wfkey_data() # Gọi để tạo file nếu chưa có
    try:
        with open(LSA_FILE, "a", encoding="utf-8"):
            pass
        with open(LSU_FILE, "a", encoding="utf-8"):
            pass
    except IOError as e:
        print(f"Không thể tạo file log: {e}")

    get_bot_info()
    polling_thread = threading.Thread(target=polling_with_retry)
    polling_thread.start()

