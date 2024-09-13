from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import os
import time
import google.generativeai as genai

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
line_handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"


genai.configure(api_key="AIzaSyD8OG39WRzCydCU2l6qOmqLJkldMbFmI9o")

def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini.

    See https://ai.google.dev/gemini-api/docs/prompting_with_media
    """
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file

def wait_for_files_active(files):
    """Waits for the given files to be active.

    Some files uploaded to the Gemini API need to be processed before they can be
    used as prompt inputs. The status can be seen by querying the file's "state"
    field.

    This implementation uses a simple blocking polling loop. Production code
    should probably employ a more sophisticated approach.
    """
    print("Waiting for file processing...")
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(10)
            file = genai.get_file(name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")
    print("...all files ready")
    print()

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash-8b-exp-0827",
  generation_config=generation_config,
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
)

chat_session = model.start_chat(
  history=[
    {
      "role": "model",
      "parts": [
        "--- START OF FILE FAQ Testing ---\n\nquestion,answer\n什麼是 @Zone，我需要付費使用嗎？,\"@Zone 是 Horizon Fitness 為了提供會員更好的運動體驗所打造的健身 App 。你可免費使用例行鍛鍊（Manual）、Sprint 8 功能。\n\n我們也提供你每月 300 Z Minute 會員專屬運動旅程點數，讓你隨心所欲安排虛擬實境（Virtual Active）及隨選播放（On-Demand），享受你的運動時光。若免費點數用盡，我們也提供方案讓你能付費購買。\n\n部分國家/地區不支援 Z Minute 、虛擬實境（Virtual Active）及隨選播放（On-Demand）功能。\"\n如何變更我的 ＠Zone 語言設定？,\"若你的行動裝置為 iOS 版本，請參考以下步驟：\n1.若你為初次設定請先至行動裝置的「設定」>「語言與地區」>「其他語言」，新增你需要更改的語言。\n2.至「個人資訊」（Profile）點擊「個人帳號與頭像」。\n3.點擊右上角的「編輯」。\n4.點擊「更換語言」，跳轉至 iOS 系統設定。\n5.點擊「語言」，選取你欲修改的語言後，返回 ＠Zone 即可修改完成。\n\n\n若你的行動裝置為 Android 版本，請參考以下步驟：\n1.至「個人資訊」（Profile）點擊「個人帳號與頭像」。\n2.點擊右上角的「編輯」。\n3.點擊語言欄位即會展開選單，可選擇你欲修改的語言。\n\n\n若您在設定過程中遇到問題，請聯繫客服。\"\n如何更新 ＠Zone ?,當 @Zone 推出新版本，當你啟動新版本即會通知你更新軟體，或者你可於 App Store 或 Google Play 搜尋「 atZone 」，出現「更新」即可點選更新。\n為什麼我的行動裝置不能安裝 ＠Zone ?,請確認你的行動裝置系統版本， @Zone 目前支援 iOS 14.0 以上(含)及 Android 5.1 以上(含)。\n如何確認我的 Horizon 健身設備支援 ＠Zone ?,\"目前 @Zone 可支援的 Horizon 的健身設備如下：\n\n跑步機：Paragon X、Omega Z、Elite T7.1、7.4AT-03、7.0AT-24、T202 SE-05、Evolve 3.0、TR3.0、TR5.0\n橢圓機：Andes 7.1、Andes 5.1、Syros 3.0、EX59-24、\n健身車／飛輪：GR7、7.0IC-22、7.0IC-21、5.0IC-21、C101-21、Paros 3.0\"\n如何新增我的 Horizon 健身設備？,\"我們透過藍牙功能連接你的行動裝置與 Horizon 健身設備，請透過下列步驟新增：\n\n1. 請將你的 Horizon 健身設備已插上電源並開啟 。\n2. 請確認你的行動裝置已開啟藍牙功能，並開啟 ＠Zone。\n3. 你可以選擇「運動」中的任一項目，點選開始，新增你的健身設備；也可以在「健身設備」右上角的「＋」鍵，點擊連接。\n4. 若你的行動裝置為 Android 版本，請在第一次新增時，允許 ＠Zone 存取你的裝置的位置資訊。\n5. 你的行動裝置將開始搜尋週遭可連線的 Horizon 健身設備，並將顯示於清單上。\n6. 點選你本次欲連接的 Horizon 健身設備，即可連線完成。\n\n**請注意**：若新增設備時遇到問題，請確認設備是否已開啟且藍牙功能正常，並嘗試重新啟動裝置和 ＠Zone 應用程式。\"\n如何移除我的 Horizon 健身設備？,\"你可以透過以下步驟，移除你的 Horizon 健身設備：\n\n1. 在「健身設備」中，點擊你的健身設備圖片至「More」視窗。\n2. 接著請你點擊「Forget Equipment」。\n3. 確認要忘記你的健身設備後，點擊「忘記」即可移除。\n\n\n**請注意**：移除設備後，您將無法再使用該設備進行運動，若您需要重新使用，請重新新增。 \"\n為什麼 @Zone 無法連上我的 Horizon 健身設備？,\"若你的 Horizon 健身設備無法與 @Zone 連結，請確認以下情況：\n\n1. 你的 Horizon 健身設備支援 ＠Zone。\n2. 健身設備有插上電源並開啟。\n3. 你的行動裝置已開啟藍牙功能。\n4. 你可以嘗試 Forget Equipment 再重新新增設備。\n5. 若你的行動裝置為 Android 版本，請於「設定」>「應用程式」中，搜尋「atZone」，於隱私設定的「許可」處檢查是否允許存取你的位置，並檢查行動裝置是否有開啟位置功能。\n\n**請注意**：若以上步驟無法排除，請聯繫客服。\"\n為什麼我的虛擬實境（Virtual Active）及隨選播放（On-Demand）影片，出現緩衝處理、停頓或無法正常播放？,\"影片出現緩衝處理、停頓或無法正常播放的情況，可以試著透過下列方法修正問題。\n\n1. 每部影片皆有對應的 Z Points ，請你確認帳戶中的 Z Points 餘額是否足夠播放影片，若餘額不足你可透過應用程式內購買 Z Points 。\n\n2. 檢查網路速度，如果網際網路連線速度較慢，影片可能無法正常播放。\n\n3. 請確認你是否已開啟手機藍牙設定並已與你的運動設備正確連接。\n\n4. 重新啟動裝置。\n\n5. 至 App Store 或 Google Play 進行應用程式更新。\n\n**請注意**：若您仍無法解決問題，請聯繫客服。\"\n我如何申請註冊？,\"請你開啟 ＠Zone 至登入頁，點擊註冊，跟隨以下步驟：\n\n1.請同意隱私權政策與使用條款。\n2.請填入你欲註冊的帳號，帳號為你的電子郵件。\n3.請填入你欲註冊的密碼，密碼須包含至少 8 個字元、至少一個數字（ 0- 1 ）、同時包含英文字母大小寫（ Ａ-Z  和 a-z ）。\n4.我們會將驗證碼寄送至你的信箱，請在 30 分鐘內輸入驗證碼以啟動你的帳號。\n5.請輸入你的個人資訊，送出後即可成功註冊。\n\n\n**請注意**：若您在註冊過程中遇到問題，請聯繫客服。\"\n我可以在不同行動裝置中登入我的帳號嗎？,可以，不論是 iOS 或 Android 系統，你皆可以在不同裝置中使用同一組帳號。\n為什麼我申請註冊後，沒有收到驗證信？,\"若你未收到 ＠Zone 發送的驗證信，可能有下列情況：\n\n1.可能是你填寫的 Email 帳號無效或輸入錯誤，你可使用正確的 Email 再次註冊。\n2.可能是你的 Email 服務商判斷驗證信為垃圾信，建議你至垃圾郵件匣中查找，並將它設定為非垃圾郵件。\n3.可能是你的 Email 服務商之安全機制阻擋驗證信，建議你可聯絡你的 Email 服務商或是使用其他的 Email 帳號重新註冊。\n4.若你使用公司 Email 註冊，請確認貴公司之資訊安全政策不會阻擋信件。\n\n\n**請注意**：若您仍無法收到驗證信，請聯繫客服。\"\n為什麼我的驗證碼驗證失敗？,\"1.請再次確認你的驗證碼是否輸入正確\n2.驗證碼超過30分鐘便會失效，請重新申請寄送驗證碼\n\n\n**請注意**：若您仍無法驗證，請聯繫客服。\"\n忘記我的密碼怎麼辦？,你可以在登入頁面的「忘記密碼」中，輸入註冊的電子郵件地址，我們會將重設密碼的認證碼寄送至你的電子信箱，請在 30 分鐘內，依照指示輸入認證碼，即可重新設定。\n\n\n**請注意**：若您在重設密碼過程中遇到問題，請聯繫客服。\"\n如何變更我的密碼、個人資料？,如果你需要變更密碼、個人資料，請至「個人資訊」內點選「編輯」，依照指示輸入即可進行重新設定。\n\n\n**請注意**：若您在變更個人資料過程中遇到問題，請聯繫客服。\"\n我可以刪除我的帳號嗎？,\"你可以_x0008_刪除在 ＠Zone 註冊的帳號，請注意刪除帳戶後所有資料將會被清除，且無法還原帳戶。\n\n你可以透過以下步驟刪除帳號：\n\n1.至「個人資訊」（ Profile ）點擊「個人帳號與頭像」。\n2.點擊右上角的「編輯」。\n3.在選單最下方點擊「刪除帳號」。\n\n\n**請注意**：刪除帳戶後，您的運動紀錄、虛擬實境及隨選播放等資料將會被清除，請務必確認是否要刪除帳號。\"\n什麼是虛擬實境？,\"虛擬實境是我們特製的互動課程，在運動過程中你的設備將會隨著影片自動調整速度、坡度或阻力，讓你在揮汗的同時享受全球各地風景，帶來身歷其境的獨特運動體驗。\n\n目前我們提供全球 22 條經典路線，供你進行訓練，我們未來也會持續更新，提供你更多選擇。\n\n部分國家 / 地區不支援虛擬實境（Virtual Active）功能。\n\n\n**請注意**：虛擬實境需要額外的 Z Minute 點數，請確認您有足夠的點數。\"\n虛擬實境支援哪些 Horizon 健身設備？,\"目前可支援的 Horizon 的健身設備如下：\n\n跑步機：Omega Z、TR3.0、TR5.0、Evolve 3.0\n\n室內健身車／飛輪：GR7、\n\n\n**請注意**：若您想使用虛擬實境，請確認您的健身設備是否支援。\"\n我該如何選擇虛擬實境的等級 ？,虛擬實境中共分為20個等級，我們建議你可先評估身體狀況及欲達到的健身目標來選擇適合的運動強度。\n\n\n**請注意**：不同的等級會對應不同的運動強度，請選擇適合自己的等級。\"\n什麼是 Sprint 8？,Sprint 8 是喬山獨家研發的訓練系統，經過科學實證，藉由 20 分鐘的高強度間歇訓練課程，能提升能量、減少體脂肪並增長肌肉。此訓練包含高強度的短暫爆發運動（ 30 秒），並接著 90 秒動態休息。\n\n\n**請注意**：Sprint 8 是一種高強度的訓練，請務必先評估自己的身體狀況，並選擇適合自己的難度。\"\nSprint 8 支援哪些 Horizon 健身設備？,\"Sprint 8 目前只支援具備坡度（ Incline ）調整功能的 Horizon 跑步機系列，及室內健身車/飛輪。\n\n跑步機：Omega Z、TR5.0\n\n室內健身車／飛輪：GR7\n\n\n**請注意**：若您的健身設備不支援 Sprint 8，您將無法使用此功能。\"\n我該如何選擇Sprint 8 的難度與等級？,\"Sprint 8 中以衝刺、動態恢復與緩和運動的速度、坡度或阻力共分為 4 個難度， 20 個等級，我們建議你可先評估身身體狀況及欲達到的健身目標來選擇適合的運動強度。\n\n初級：等級 1 ～ 5\n適中：等級 6 ～ 10\n進階：等級 11 ～ 15\n精英：等級 16 ～ 20\n\n\n**請注意**：不同的難度與等級會對應不同的運動強度，請選擇適合自己的難度與等級。\"\n什麼是配速訓練，我該如何設定？,\"配速是長跑訓練中常被使用的概念，通常指每公里跑步所用的時間。\n\n利用配速訓練，你可以更精確地調整運動節奏、體能訓練，更有效率地突破自我極限。\n\n你可以依據自身體能狀況及訓練需求，設定不同段落的時速與時間，最多可設定 10 個分段。\n\n\n**請注意**：配速訓練需要一定的跑步經驗，請務必先評估自己的身體狀況，並選擇適合自己的配速。\"\n什麼是目標心率訓練，＠Zone可以如何幫助我達成？,\"目標心率是一個用來測量運動強度的指標，你可以設定運動時間、目標心率，＠Zone 透過調整 Horizon 健身設備的坡度、阻力、速率，來幫助你達到目標。\n\n此訓練需要另外連接心率胸帶才能正確執行。\n\n關於目標心率如何計算，可以用你的最大心率乘以運動強度%得出。\n\n運動強度定義可以參考美國心臟協會（ American Heart Association ）建議：\n中強度運動：最大心率的 50 ～ 70 ％\n高強度運動：最大心率的 70 ～ 85 ％\n\n\n**請注意**：目標心率訓練需要正確佩戴心率胸帶，並設定正確的心率目標。 \"\n如何連接我的心率胸帶？,\"正確穿戴好你的心率胸帶，開啟行動裝置藍牙功能後，你可以透過以下 2 種方法連接至 @Zone：\n\n方法1：\n\n在「運動」＞「訓練」＞「目標心率」中的心率胸帶，點擊「連接」\n\n方法2：\n\n1.在「個人資訊」＞「連線裝置」，點擊右上角編輯符號。\n\n2.在「編輯裝置」中，點擊右上角的「＋」。\n\n3.選取你的裝置，並點擊「Add」。\n\n\n**請注意**：若您在連接心率胸帶時遇到問題，請確認心率胸帶是否正確穿戴，並確認行動裝置藍牙功能是否正常。\"\n為什麼我的心率胸帶無法連接 ＠Zone ?,\"若你的心率胸帶無法與 ＠Zone 連接，可能有下列情況：\n\n1.請確認你的心率胸帶穿戴正確。\n\n2.請確認你的心率胸帶電源充足。\n\n3.可能是你的行動裝置未開啟藍牙功能。\n\n\n**請注意**：若您在連接心率胸帶時遇到問題，請確認心率胸帶是否正確穿戴，並確認行動裝置藍牙功能是否正常。  若問題依然存在，請聯繫客服。\"\n什麼是隨選播放？,\"Horizon Fitness 為你邀請全球熱門教練，超過上百堂課程持續更新，讓你在家即可隨選播放課程，跟著教練豐富你的訓練，加乘運動效果。\n\n部分國家 / 地區不支援隨選播放（On-Demand）功能。\n\n\n**請注意**：隨選播放需要額外的 Z Minute 點數，請確認您有足夠的點數。\"\n隨選播放支援哪些 Horizon 健身設備？,不同的隨選播放課程，會搭配不同的健身設備，請至隨選播放詳情頁面，查看該課程所支援之設備。\n\n\n**請注意**：若您想使用隨選播放，請確認您的健身設備是否支援。\"\n為什麼隨選播放課程不支援我的語言？,我們正陸續更新隨選播放課程語言，敬請期待！\n\n\n**請注意**：若您想使用隨選播放課程，請確認您的 ＠Zone 應用程式是否支援您的語言。\"\n什麼是加入比賽？我可以與誰一起競賽？,\"你可以在虛擬實境（Virtual Active）和 Sprint 8 中，與全球使用者一起競賽，系統將會綜合你訓練時的坡度、心率、燃燒的卡路里等綜合計算出Sweat Score，完成後即可看到你於本次運動後的成績！\n\n路線開始時，你會在畫面上看到你及自身成績前後兩位使用者與你同場較勁。\n\n\n**請注意**：加入比賽需要額外的 Z Minute 點數，請確認您有足夠的點數。\"\n什麼是Sweat Score ?,Sweat Score 是依據你訓練時的坡度或阻力、心率及燃燒的卡路里等綜合計算出的運動成績\n\n\n**請注意**：Sweat Score 是用來評估你的運動表現，可以幫助你了解自己的運動進度。\"\n如何查看、分享我過去的運動紀錄？,\"你可以在「個人資訊」＞「運動紀錄」中，查看與分享你的運動時間、消耗卡路里與運動摘要。\n或者在運動結束後， ＠Zone 會為你整理本次運動摘要，你可以透過分享按鍵，與你的親朋好友分享。\n\n\n**請注意**：運動紀錄會記錄您的運動時間、消耗卡路里、Sweat Score 等資訊，您可以透過這些資訊來追蹤自己的運動進度。\"\n為什麼連接的 Horizon 健身設備的數據，與 ＠Zone 上呈現的數據不同？,因為藍牙傳輸時間限制偶爾會造成此情況，但不影響你最終運動數據。\n\n\n**請注意**：藍牙傳輸數據可能會存在延遲，但不會影響您的運動數據。\"\n如何將@Zone 連接到第三方應用程序？,\"@Zone現在支援Apple Health、Google Fit、Fitbit和Strava等第三方應用程式。連接您最喜愛的應用程式，並無縫整合您的健身數據。\n1..至「個人資訊」（Profile。\n2.點擊「連接APP」。\n3.選擇您想連接的第三方軟體，按下「連接」。\n4. 根據第三方軟體指示完成連接。\n\n\n**請注意**：連接第三方應用程式需要您同意 ＠Zone 應用程式訪問您的健身數據。 \"\n\n--- END OF FILE FAQ Testing ---",
      ],
    },
    {
      "role": "user",
      "parts": [
        "超出FAQ範圍請說: 請詢問關於atZone相關問題",
      ],
    },
    {
      "role": "model",
      "parts": [
        "很抱歉，我無法回答這個問題。它超出了我的 FAQ 範圍。\n\n請詢問關於 atZone 相關問題。\n",
      ],
    },
  ]
)




app = Flask(__name__)


# domain root
@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global working_status
    if event.message.type != "text":
        return

    if event.message.text == "說話":
        working_status = True
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="我可以說話囉，歡迎來跟我互動 ^_^ "))
        return

    if event.message.text == "閉嘴":
        working_status = False
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="好的，我乖乖閉嘴 > <，如果想要我繼續說話，請跟我說 「說話」 > <"))
        return

    if working_status:
        msg=str(event.message.text)
        response = chat_session.send_message(msg)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(response.text))


if __name__ == "__main__":
    app.run()
