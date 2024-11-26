import cv2
import numpy as np 
import mediapipe as mp 
import HandTrackingModule as htm
import time 
import pyautogui


##########################
wCam, hCam = 640, 480
frameR = 100 # Frame Reduction
smoothening = 7
#########################


cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0

plocX, plocY = 0, 0
clocX, clocY = 0, 0


detector = htm.handDetector(maxHands=1)
wScr, hScr = pyautogui.size() 



while True: 
    # 1. Find hand Landmarks
    success, img = cap.read()
    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img)
    

    # 2. Get the tip of the index finger and middle finger 
    if len(lmList)!= 0:
        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]

        #print(x1, y1, x2, y2)

        # 3. Check which fingers are up
        fingers = detector.fingersUp()
        #print(fingers)

        # Setting Rectangle Frame 
        cv2.rectangle(img,(frameR, frameR), (wCam-frameR, hCam-frameR), (255,0,255),2)

        # 4. Only index finger in the Moving mode
        if fingers[1] == 1 and fingers[2] == 0:


        # 5. Convert Coordinates 
            x3 = np.interp(x1, (frameR,wCam-frameR),(0,wScr))
            y3 = np.interp(y1, (frameR,hCam-frameR),(0,hScr))


        # 6. Smoothen Values 
            clocX = plocX + (x3 - plocX) / smoothening
            clocY = plocY + (y3 - plocY) / smoothening


        # 7. Move Mouse 
            pyautogui.moveTo(wScr - clocX, clocY)
            cv2.circle(img, (x1,y1),15,(255,0,255),cv2.FILLED)
            plocX, plocY = clocX, clocY
        

    # 8. Both Index finger and Middle finger are up, CLICKING mode 
    
        # 9. Find distance between these fingers 
        # Detect fingers
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0:
            # Two fingers up (index and middle) - Left click
            length, img, lineinfo = detector.findDistance(8, 12, img)
            if length < 40:
                cv2.circle(img, (lineinfo[4], lineinfo[5]), 15, (0, 255, 0), cv2.FILLED)
                pyautogui.click(button='left')  # Left click

        elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1:
            # Three fingers up (index, middle, and ring) - Right click
            length, img, lineinfo = detector.findDistance(8, 12, img)
            if length < 40:
                cv2.circle(img, (lineinfo[4], lineinfo[5]), 15, (0, 0, 255), cv2.FILLED)
                pyautogui.click(button='right')  # Right click

    

    # 11. Frame Rate 
    cTime = time.time()
    fps = 1/(cTime - pTime)
    pTime = cTime
    cv2.putText(img, str(int(fps)), (20,50), cv2.FONT_HERSHEY_PLAIN, 3, (255,0,255),3)

    # 12. Display 
    cv2.imshow("Image", img)
    cv2.waitKey(1)


