import cv2
import numpy as np
import HandTrackingModule as htm
import time
import autopy
import math
import webbrowser
import pyautogui
import cvzone
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from time import sleep
from pynput.keyboard import Controller

#########################
wCam, hCam = 1280, 720
frameR = 100  # Frame Reduction
smoothening = 4
#########################

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0
flag = 0

detector = htm.handDetector(detectionCon=1, maxHands=1)
wScr, hScr = autopy.screen.size()
keys = [["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"]]

keyboard = Controller()

# 功能1：音量控制
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
# volume.GetMute()
# volume.GetMasterVolumeLevel()
volRange = volume.GetVolumeRange()
minVol = volRange[0]
maxVol = volRange[1]
vol = 0
volBar = 400
volPer = 0

# 功能3：虚拟键盘
def drawAll(img, buttonList):
    imgNew = np.zeros_like(img, np.uint8)
    for button in buttonList:
        x, y = button.pos
        cvzone.cornerRect(imgNew, (button.pos[0], button.pos[1], button.size[0], button.size[1]),
                          20, rt = 0)
        cv2.rectangle(imgNew, button.pos, (x + button.size[0], y + button.size[1]),
                      (255, 0, 255), cv2.FILLED)
        cv2.putText(imgNew, button.text, (x + 60, y + 80),
                    cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 3)

    out = img.copy()
    alpha = 0.5
    mask = imgNew.astype(bool)
    print(mask.shape)
    out[mask] = cv2.addWeighted(img, alpha, imgNew, 1 - alpha, 0)[mask]
    return out


class Button():
    def __init__(self, pos, text, size = [85, 85]):
        self.pos = pos
        self.size = size
        self.text = text


buttonList = []
for i in range(len(keys)):
    for j, key in enumerate(keys[i]):
        buttonList.append(Button([100 * j + 150, 100 * i + 320], key))


while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img)
    #img = drawAll(img, buttonList)
    #print(lmList)



    # 功能1：音量控制
    if len(lmList) != 0:
        if len(lmList) > 8:
            x1, y1 = lmList[4][1], lmList[4][2]
            x2, y2 = lmList[8][1], lmList[8][2]
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            fingers = detector.fingersUp()
            if fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0:
                cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
                cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
                cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
                cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

                length = math.hypot(x2 - x1, y2 - y1)
                # print(length)

                # Hand range 50 - 300
                # Volume Range -65 - 0

                vol = np.interp(length, [50, 300], [minVol, maxVol])
                volBar = np.interp(length, [50, 300], [400, 150])
                volPer = np.interp(length, [50, 300], [0, 100])
                print(int(length), vol)
                volume.SetMasterVolumeLevel(vol, None)

                if length < 50:
                    cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)

    cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)
    cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                1, (255, 0, 0), 3)


    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX,
                1, (255, 0, 0), 3)



    # 功能2：虚拟鼠标
    # 2.找到指尖
    if len(lmList) != 0:
        x3, y3 = lmList[8][1:]
        x4, y4 = lmList[12][1:]
        # print(x3, y3, x4, y4)

        # 3.检测抬起的手指
        fingers = detector.fingersUp()
        # print(fingers)
        cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR),
                      (255, 0, 255), 2)
        # 4.只有食指是移动模式
        if fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 0:
            # 5.转换坐标
            x5 = np.interp(x3, (frameR, wCam - frameR), (0, wScr))
            y5 = np.interp(y3, (frameR, hCam - frameR), (0, hScr))

            # 6.平滑值
            clocX = plocX + (x5 - plocX) / smoothening
            clocY = plocY + (y5 - plocY) / smoothening
            # 7.移动鼠标
            if any(buttonList[0].pos[0] < x3 < buttonList[9].pos[0] + buttonList[0].size[0] and
                   buttonList[0].pos[1] < y3 < buttonList[29].pos[1] + buttonList[29].size[1] for button in
                   buttonList) and flag == 1:
                pass

            else:
                autopy.mouse.move(wScr - clocX, clocY)
            cv2.circle(img, (x3, y3), 15, (255, 0, 255), cv2.FILLED)
            plocX, plocY = clocX, clocY
        # 8.点击模式
        if fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 1:
            # 9.两指距离
            length, img, lineinfo = detector.findDistance(8, 12, img)
            #print(length)
            # 10.点击判定
            if length < 38:
                cv2.circle(img, (lineinfo[4], lineinfo[5]),
                           15, (0, 255, 0), cv2.FILLED)
                autopy.mouse.click()

    # 11.帧率
    #cTime = time.time()
    #fps = 1 / (cTime - pTime)
    #pTime = cTime
    #cv2.putText(img, str(int(fps)), (20, 50), cv2.FONT_HERSHEY_PLAIN, 3,
                #(255, 0, 0), 3)



    # 功能3：虚拟键盘
    # 现在需要用cv2.rectangle创建一个按钮
    #img = drawAll(img, buttonList)
    showbutton = Button([600, 40],"Show")
    cv2.rectangle(img, showbutton.pos,(showbutton.pos[0]+90, showbutton.pos[1]+40),(255,0,255),cv2.FILLED)
    cv2.putText(img, showbutton.text,(showbutton.pos[0]+3, showbutton.pos[1]+27),
                cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)

    if lmList is not None :
        if len(lmList) >= 21:
            l1,_,_= detector.findDistance(8,12,img,draw = False)

            if ((showbutton.pos[0])< lmList[8][1] < (showbutton.pos[0]+90)
                    and (showbutton.pos[1]) < lmList[8][2] < (showbutton.pos[1]+40)
                    and l1<28):

                sleep(0.5)
                flag = abs(flag-1)

            if flag == 1:
                cv2.rectangle(img, showbutton.pos, (showbutton.pos[0] + 90, showbutton.pos[1] + 40), (255, 0, 255),
                              cv2.FILLED)
                cv2.putText(img, "Hide", (showbutton.pos[0] + 3, showbutton.pos[1] + 27),
                            cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)
                img = drawAll(img, buttonList)
                for button in buttonList:
                    x, y = button.pos
                    w, h = button.size
                    #print(handLMs[8][1],handLMs[8][2])
                    if x < lmList[8][1] < x + w and y < lmList[8][2] < y + h:
                        cv2.rectangle(img, button.pos, (x + w, y + h), (175, 0, 175), cv2.FILLED)
                        cv2.putText(img, button.text, (x + 20, y + 65),
                                    cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
                        l,_,_= detector.findDistance(8,12,img,draw = False)
                        #print(l)

                        if l<30:
                            keyboard.press(button.text)
                            cv2.rectangle(img, button.pos, (x + w, y + h), (0, 255, 0), cv2.FILLED)
                            cv2.putText(img, button.text, (x + 20, y + 65),
                                        cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
                            sleep(0.35)


        # 功能4：一键打开百度/GitHub
        if lmList is not None:
            if len(lmList) >= 21:
                l2, _, _ = detector.findDistance(12, 16, img, draw = False)
                fingers = detector.fingersUp()
                if fingers[0] == 0 and fingers[1] == 0 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 1:
                    if l2 < 38:
                        webbrowser.open('www.baidu.com')
                        sleep(1.5)

        # 功能5 最大化/最小化窗口
        if lmList is not None:
            if len(lmList) >= 21:
                fingers = detector.fingersUp()
                l3, _, _ = detector.findDistance(4, 8, img, draw = False)
                l4, _, _ = detector.findDistance(8, 12, img, draw = False)
                l5, _, _ = detector.findDistance(12, 16, img, draw = False)
                l6, _, _ = detector.findDistance(16, 20, img, draw = False)
                l7, _, _ = detector.findDistance(4, 20, img, draw = False)
                #print(l3, l4, l5, l6, l7)

                if fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 1:
                    sleep(0.5)
                    pyautogui.hotkey('alt', 'space')
                    pyautogui.press('x')
                    sleep(1)

                if fingers[0] == 0 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                    if l3<23 and l4<54 and l5<36.5 and l6<34 and l7<100:
                        sleep(0.5)
                        pyautogui.hotkey('win', 'down')
                        sleep(1)


    cv2.imshow("Img", img)
    cv2.waitKey(1)