import datetime as dt
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

D = lambda s: dt.date.fromisoformat(s)
CATS = {1:"Delivery delay",2:"Order not received",3:"Marked delivered but not received",4:"Tracking/status issue",
5:"Courier/delivery attempt issue",6:"Lost/returned shipment",7:"Missing item",8:"Partial shipment",9:"Wrong item",
10:"Damaged item",11:"Leaking/empty/tampered product",12:"Expired/near-expiry product",13:"Cancellation",14:"Refund delay",
15:"Incorrect/partial refund",16:"Refund not received",17:"Replacement problem",18:"Customer-support accessibility",
19:"Customer-support resolution failure",20:"Other order/fulfillment issue"}
def grp(c):
    if c<=6: return "WISMO core"
    if c<=12: return "Adjacent fulfilment"
    if c<=17: return "Cancellation/refund"
    if c<=19: return "Support"
    return "Other"
BASE = {1:"Medium",2:"High",3:"Critical",4:"Medium",5:"Medium",6:"High",7:"High",8:"High",9:"High",10:"Medium",11:"Medium",
12:"Medium",13:"High",14:"Medium",15:"High",16:"High",17:"High",18:"Medium",19:"Medium",20:"Medium"}
MONEY = {2,3,6,7,8,9,13,15,16}
LV = ["Low","Medium","High","Critical"]
def sev(c, fl):
    s = LV.index(BASE[c])
    if "X" in fl and ("R" in fl or c in MONEY): s = min(3, s+1)
    return LV[s]
STAGE = {1:"In transit",2:"In transit",3:"Delivered",4:"In transit",5:"Out for delivery",6:"In transit",7:"Post-delivery",
8:"Post-delivery",9:"Post-delivery",10:"Post-delivery",11:"Post-delivery",12:"Post-delivery",13:"Order placed/confirmed",
14:"Refund / replacement",15:"Refund / replacement",16:"Refund / replacement",17:"Refund / replacement",18:"Support",
19:"Support",20:"Order placed/confirmed"}
JOURNEY = {"Order placed/confirmed":"Order","Packed/Shipped":"Shipping","In transit":"Shipping","Out for delivery":"Delivery",
"Delivered":"Delivery","Post-delivery":"Post-delivery","Refund / replacement":"Refund","Support":"Support"}

TP="https://dk.trustpilot.com/reviews/"
VX="https://voxya.com/consumer-complaints/"
AP="https://apps.apple.com/in/app/smytten-try-samples-shop/id1100171914?see-all=reviews&platform=iphone"
MS="https://www.mouthshut.com/review/smytten-review-"
IC="https://www.indiacustomercare.com/smytten-customer-care-no#comment-"

# id,date,source,url,author,cat,sec,flags,ES,fragment,summary,dupgroup,dupstatus,stage_override,date_verified
R=[]
def a(*x): R.append(x)
T="Trustpilot"
a("TP-01","2026-09-10",T,TP+"6aa29e8884889e77a0b9c27f","Varun Jain",2,"16,13,18","SRDX","High","it wasnt delivered, neither I was able to cancel it","Rakhi gift hamper (Rs 1,400) undelivered; cancellation impossible; refund chased for 10 days via chat only","","unique","","Yes")
a("TP-02","2026-08-29",T,TP+"6a9255df449fbbbb2ae69e2f","manik sambyal",19,"9,8","SDX","Medium","even receive the complete order at all","Reports complaints answered with a 'we shipped what was ordered' line; doubts correct/complete delivery","","unique","","Yes")
a("TP-03","2026-08-22",T,TP+"6a89b161f76e750e56c9209d","Himanshi",1,"16,4","DR","Medium","I still have not received my order","Paid; 15 days without delivery or update; asks for refund","","unique","","Yes")
a("TP-04","2026-07-19",T,TP+"6a5cb9e5e0d332a1f509db99","Consumer (CO)",2,"16,18,19","SRDX","High","order ni aya 10 bar hmne msg krke pucha","Hinglish: June order undelivered after a month; 10 chat queries; refund promised, not paid; no contact number","","unique","","Yes")
a("TP-05","2026-04-03",T,TP+"69cf5c428096bfd82fa9c878","Saranya Nair",9,"19","SDX","High","the issue was denied without resolution","Wrong/unusable item on a Rs 140 order; proof sent; 4 days of follow-ups; claim denied","","unique","","Yes")
a("TP-06","2026-03-11",T,TP+"69b15f56c26f87bdbb88076d","Dolly Chauhan",9,"18","SDX","Medium","They don’t send the products you order","Says substitute trial items are sent instead of ordered products; support unresponsive","","unique","","Yes")
a("TP-07","2026-03-07",T,TP+"69abb446cd95ebb306be82fa","Laxman Bishnoi",9,"19,18","SDX","High","the products have been dispatched & delivered correctly from our end","Wrong items on a shop order; bot ticket closed as 'delivered correctly'; no phone or escalation; emails unanswered","","unique","","Yes")
a("TP-08","2026-01-24",T,TP+"697472a0c667aaccdbafa8be","Pavitarjit Kaur",9,"","D","Low","I got wrong products","States wrong products received; no further detail","","unique","","Yes")
a("TP-09","2025-12-26",T,TP+"694e6d235ff12281d8b1317e","Aditi Badoni",3,"","DR","Medium","they are saying uts delivered how","Paid trial packs shown delivered but not received; wants refund or parcel","","unique","","Yes")
a("TP-10","2025-12-26",T,TP+"694e213eba6301bb0fff96e3","preeti azad",13,"16","R","Medium","My main orders automatically cancelled","Main orders auto-cancelled; refund withheld citing trial price","","unique","","Yes")
a("TP-11","2025-11-03",T,TP+"6908ad3ac07e5d93ab3aee5a","DONTHI RAJU",8,"17,19","SDX","High","does not fall under policy guidelines","4 roll-ons ordered, 2 sent; reshipment gave 1; claim rejected as outside policy","","unique","","Yes")
a("TP-12","2025-06-04",T,TP+"683fe2558479112dba244381","Manisha Joshi",16,"20,18","SRX","High","my money got deducted and order id not generated","Rs 244 debited, no order ID, no refund; care line and email unanswered","","unique","","Yes")
a("TP-13","2025-04-23",T,TP+"6808bb14180e05932ab06e10","Shaikh Saniya",11,"20,19","SDX","High","received a used face razor and a leaked keratin shampoo","Used razor and leaking shampoo delivered; email/Instagram contacts ignored; ticket marked resolved","","unique","","Yes")
a("TP-14","2025-04-14",T,TP+"67fcf52b987f99326190a2f1","saher tamanna",9,"19","SDX","Medium","Received a different product","Different product received; ticket marked resolved without a fix","","unique","","Yes")
a("TP-15","2025-03-22",T,TP+"67de461dcbe98cd2d7fc2bef","Saumya Shukla",1,"18","DSX","Medium","ordered my products last 9 days","Paid; 9 days undelivered; email unanswered; chat handled by AI","","unique","","Yes")
V="Voxya"
a("VX-01","2025-12-23",V,VX+"product-not-delivered-/255688","Nandana v k",3,"19","DSX","High","did not receive any call or communication from your delivery team","Out-for-delivery mail then 'delivered' message; no call or attempt; email unanswered","","unique","","Yes")
a("VX-02","2025-10-28",V,VX+"package-not-delivered/252807","Kavish",1,"4,13","D","High","smytten didn't provide delivery partner and it is delayed very day","Prepaid; ETA slips daily; tracking dates conflict across sites; cannot cancel","","unique","","Yes")
a("VX-03","2025-12-30",V,VX+"delivered-but-not-received-order-/256099","Rashmita padhy",3,"18","DSRX","High","The app is not allowing me to raise a ticket.","Shown delivered, not received; app blocks ticket; asks re-delivery or refund","","unique","","Yes")
a("VX-04","2025-12-25",V,VX+"package-not-delivered-but-showing-delivered-/255787","purvanshi patel",3,"","DR","Medium","I have not recieved any calls from delivery partner","SMS and app show delivered; no courier call; wants delivery or refund","DUP-01","unique","","Yes")
a("VX-05","2025-12-26",V,VX+"package-not-delivered-/255806","Pavitra",3,"","DR","Medium","I have not recieved any calls from delivery partner","Near-identical text to VX-04 one day later (counted once)","DUP-01","duplicate","","Yes")
a("VX-06","2025-12-29",V,VX+"refund-not-reflected-in-my-account-/256000","Kunal Gaikwad",16,"13","SRX","High","they show refund initiated but it didn't reflected into my account","Cancelled within minutes (no address edit); refund 'initiated' not credited; mail unanswered","","unique","","Yes")
a("VX-07","2026-01-06",V,VX+"refund-pending-due-to-incorrect-order-status-/256565","Akanksha Singh",4,"16,19","SRDX","High","their app has not updated the order status","Cancelled at doorstep; app still 'Shipped' so refund not started; AI chatbot loop","","unique","Refund / replacement","Yes")
a("VX-08","2026-01-16",V,VX+"refund-of-skin-care-products-which-were-not-received-/257258","Prajitarani Hiwale",16,"13","SR","Medium","my order was cancelled and the refund of it still not received","Order cancelled; refund not received; emailed Smytten","","unique","","Yes")
a("VX-09","2026-01-24",V,VX+"received-only-one-product-out-of-6-products-on-smytten-also-the-payment-was-fully-done-by-prepaid-mo/257784","Preeti Ghanekar",8,"","D","Medium","as soon as I opened my box there was only one product","Prepaid 6-product order; only 1 product arrived","","unique","","Yes")
a("VX-10","2026-07-17",V,VX+"missing-item-/270438","Nimisha Lodha",7,"19","SDX","Medium","filled a complaint but no action taken","Item missing from parcel; photos sent; told it was not Smytten's mistake","","unique","","Yes")
A="Apple App Store"
PY="Partial (year inferred from Apple date format)"
a("AP-01","2026-04-04",A,AP,"Your good wisher customer (review 'Positive, but hidden problem')",16,"13,18","SRX","Medium","my refund still not granted","Order cancelled in app; refund not granted; no support number; forwarded emails only","","unique","",PY)
a("AP-02","2025-12-23",A,AP,"1P1G",1,"13,19","SRDX","High","app is not allowing to cancel the product stating tech error","Ordered 10 Dec, promised 12 Dec, undispatched after 12 days; cancel blocked; only partial cancellation","","unique","Packed/Shipped","Yes")
a("AP-03","2025-05-05",A,AP,"Lazee₹₹",19,"1","SDX","Medium","where it’s stuck for a week almost","Ticket closed without reviewing photos; parcel stuck about a week; agent-conduct dispute","","unique","","Yes")
a("AP-04","2026-08-20",A,AP,"Nijal Nandaa",5,"6,19","SD","High","there was no delivery partner available for my area","Courier no-show; told no partner in area; asked to self-collect; order returned after 11 days","","unique","",PY)
a("AP-05","2026-07-23",A,AP,"Prat103",7,"16,18,10","SRX","High","my Glutathione effervescent tablets were missing","Tablets missing; no refund; AI-bot dead end; battered packaging","","unique","",PY)
a("MS-01","2025-12-23","MouthShut",MS+"tpqqsplupop","MouthShut user (name not captured)",3,"19","DSRX","Medium","they said it'll take 10 days to investigate","Status 'delivered' but not received; support says 10 days to investigate; no update or refund","","unique","","Partial (search-index date)")
ICN="IndiaCustomerCare (comments)"
def ic(cid,d,au,c,sec,fl,es,fr,sm,dg="",ds="unique",so=""):
    a("IC-"+cid,d,ICN,IC+cid,au,c,sec,fl,es,fr,sm,dg,ds,so,"Yes")
ic("214806","2026-03-23","Anonymous",3,"","D","Medium","it shows delivered but I didn't receive the order","Paid order shown delivered, not received")
ic("213885","2026-01-22","Angitha",2,"16,19","SRDX","High","I raised a ticket but not showing in my account","Trial pack paid 24 Dec, promised 2 Jan, undelivered on 22 Jan; ticket invisible; no refund")
ic("213773","2026-01-17","Zainab khanum",4,"1,18","SRDX","Medium","not updating the delivery dates","Delivery dates not updated; calls and mail unanswered; wants refund")
ic("213755","2026-01-16","Anonymous",3,"","D","Medium","showing order delivered,but didn't receive order","Order section shows delivered; not received")
ic("213684","2026-01-13","ANKITA",3,"19","SRDX","High","I WANT MY REFUND OR ORDER","Trial order shown delivered 26 Dec (due 29 Dec); repeated emails/tickets unresolved")
ic("213681","2026-01-13","Rozi",5,"19","SDX","High","it has a wrong number in my parcel","Prepaid parcel carries wrong phone number; courier needs OTP; not returned; help centre/email silent")
ic("213546","2026-01-08","Anonymous",3,"","D","Medium","My order is marked delivered but I didn't receive any order","Prepaid order marked delivered; no courier call")
ic("214709","2026-03-17","Ravi Singh",3,"","D","Low","My oder is delivered not delivered to me","Says order shown delivered but not received; asks for help")
ic("213482","2026-01-06","Ashika Priya",3,"","DR","Medium","order placed krte nhi h delivered show hone lgte","Hinglish: order shows delivered without arriving; wants delivery or refund")
ic("213449","2026-01-03","Anonymous",3,"","DR","Medium","had been showed as delivered in the app","Not delivered although app shows delivered; asks refund or re-delivery")
ic("213418","2026-01-01","Anushka verma",3,"","D","High","showing delivered on 29 December in app but i have not received yet","Ordered 22 Dec; delivered 29 Dec per app; no call or SMS; prepaid")
ic("213395","2025-12-31","Anonymous",3,"19","DSX","Medium","order didn't received and it was prepaidd no response by agents","Prepaid order marked delivered, not received; agents unresponsive")
ic("213375","2025-12-30","Vaishnavi",3,"18","D","High","before 2 of delivery it is marked delivered","Ordered 25 Dec, ETA 31 Dec, marked delivered two days early; prepaid via GPay")
ic("213370","2025-12-30","Anonymous",5,"","D","High","the delivery partner has a different contact number than mine","Courier holds wrong contact number so parcel cannot be received (order ID given)")
ic("213367","2025-12-30","Anonymous",3,"","D","High","No call from any delivery partner","Prepaid shop order shown Delivered 30 Dec; no attempt, call or handover")
ic("213366","2025-12-30","Bobby",3,"19,18","DSX","High","it was closed within a day saying matter is escalated","Marked delivered 28 Dec; ticket closed in a day with a 10-day escalation; no phone contact")
ic("213361","2025-12-30","Anjali Rajput",3,"","D","Low","Order market delivery but not recived any call and order","Shown delivered; no call; not received")
ic("213360","2025-12-30","Manju Singh",3,"5,19","DSRX","High","The number given to delhivery was false and invalid","Delivered per app and Delhivery email but courier held an invalid number; 5 days no reply; wants replacement or refund")
ic("213349","2025-12-29","Anonymous",3,"20","D","High","This same issue happened last year also","Shown delivered; neighbours checked; alleges no delivery verification; says repeat issue")
ic("213347","2025-12-29","Pranava vani",3,"18","DSX","Medium","if want to chat then it showing they are busy","Shown delivered, not received; no contact number; chat busy")
ic("213345","2025-12-29","Hemali",3,"19,18","DSX","Medium","10 bar ek issue raised kar chuki hai","Shown delivered; issue raised 10 times; AI chat repeats questions")
ic("213344","2025-12-29","Anonymous",3,"","DT","High","I have not received the package","Shown delivered 24 Dec (Hubli); not received; asks re-delivery or refund")
ic("213343","2025-12-29","Karishma",5,"4","D","Medium","Dilevery boy is not calling","Status 'out for delivery' but courier not calling")
ic("213342","2025-12-29","Alina",3,"","D","Medium","the status is showing delivered","Parcel not received; status delivered")
ic("213339","2025-12-29","Anonymous",3,"18","DSXT","High","even after having so many time chat on app they are not replying","Order ID cited; delivered 24 Dec (Noida) but not received; no call or OTP; chat and mail unanswered; 4-year customer")
ic("213337","2025-12-29","Chetana Gaonkar",3,"","D","Medium","fake delivery status in the app","Delivered 27 Dec per app; no order or call")
ic("213309","2025-12-27","Pankaj Kumar",3,"","DT","Medium","My Trial Order is showing as delivered on the app","Trial order shown delivered; no call or OTP (text identical to IC-213231)")
ic("213295","2025-12-26","Sanskriti Sapre",5,"1","D","High","just state that your address is wrong","Ordered 18 Dec; friend in same city received hers; courier claimed wrong address without calling; 8 days")
ic("213289","2025-12-26","Komal Molane",3,"","DT","High","showing as delivered on 24th December at Pune Godumbre D","Order ID cited; delivered 24 Dec (Pune) but not received; asks re-delivery or refund")
ic("213350","2025-12-29","Ashu",3,"","D","High","i am not received any OTPany Call for receive the order","Order #4821208 (25 Dec) marked delivered by 29 Dec; no OTP or call; paid")
ic("213283","2025-12-25","Ratnesh sawle",5,"","D","Low","indore city branch will not delivered","AWB cited; status suggests branch will not deliver; text garbled")
ic("213454","2026-01-04","Honey sonkhla",2,"18,16","DR","Medium","na koi agent ka call ho pa rha na costumer care se","Hinglish: paid, no delivery; cannot reach agent or care; asks refund or order")
ic("213304","2025-12-27","Diya Kotwal",3,"","DRT","Medium","The tracking status shows that the parcel has been delivered","Tracking says delivered; no agent call; full payment made")
ic("213268","2025-12-24","Niharika sen",3,"","DRT","Medium","The tracking status shows that the parcel has been delivered","Same wording as IC-213304")
ic("214760","2026-03-20","Jeevika",2,"","DR","Low","even we have made the payment but our order is not delivered yet","Reply comment: paid order (sister's) also undelivered; threatens complaint")
ic("213348","2025-12-29","Anonymous",4,"1","D","Medium","my order not delivered","Ordered 17 Dec; tracking 'stuck in the previous date'; not delivered")
ic("213252","2025-12-23","Anonymous",3,"18","DSX","High","official mail recieved me that product is delivered","Ordered 21 Dec, due 23 Dec; mail says delivered; not received; no assistance")
ic("213251","2025-12-23","Anonymous",3,"19","DSX","Medium","the app was showing delivered and no help from their side","Not received though app shows delivered; ticket and email gave no help")
ic("213249","2025-12-23","Swati from deoband",3,"18","DSX","High","its Tracking system showing it delivered","6 trials + 2 gifts paid; none received; tracking says delivered; nobody responds")
ic("213231","2025-12-21","Sonali Dubey",3,"","DT","Medium","My Trial Order is showing as delivered on the app","Trial order shown delivered; no call or OTP")
ic("213024","2025-12-06","Twinkle",1,"13","D","Medium","my order is not received yet","Promised 1 Dec; not received on 6 Dec; wants delivery or cancellation")
ic("214816","2026-03-24","Jayasree",4,"","D","Low","I can't track my order","Cannot track order (literal WISMO query)")
ic("213013","2025-12-05","Anonymous",13,"1,16","R","High","the smytten cancel my order saying it's been cancel from my side","About Rs 6,000 order; ETA extended daily then cancelled as 'user-cancelled'; refund initiated, user doubtful")
ic("212976","2025-12-02","Anonymous",16,"13","R","Medium","I told cancellation code to delivery executive person","Doorstep cancellation via code; no confirmation; refund not received")
ic("212696","2025-11-14","Meenakshi Sharma",1,"5","D","High","I should be told why the order has not been delivered till now","AWB cited; ordered 7 Nov; OTP sent then non-delivery message; Rs 314 paid")
ic("211778","2025-09-12","Sanjana yadav",7,"19","SRX","High","smytten team wrongly suggested that it was my mistake","Two Philips items missing from shop order; support blamed customer; escalation threatened","DUP-02")
ic("211760","2025-09-11","Sanjana yadav",7,"","S","High","I have sent unboxing video","Earlier post on the same missing-items incident (counted once)","DUP-02","duplicate")
ic("211314","2025-08-19","Dev Raghav",1,"4,18","DSRX","High","App didn't showed me any delayed information","Ordered 13 Aug, due 17 Aug; no delay notice; mail unanswered; paid online; wants product or money back")
ic("210937","2025-07-30","Nisha",1,"4","D","High","The location on the tracking is continuously the same","Ordered 15 Jul; tracking frozen (Bareilly) after two weeks")
ic("209499","2025-05-13","Priyadharsini H J",9,"13,15","R","High","delivered product is of 9 ml","Ordered 12 ml, received 9 ml; second order cancelled unknowingly; refunded Rs 299 of Rs 319")
ic("208769","2025-04-20","Sapna",9,"","D","Medium","they give me oats packet","Promised lip/face tint free gift; received an oats packet")
ic("208600","2025-04-16","Knchn",2,"","D","Low","My order not received","Order not received (no detail)")
ic("208026","2025-03-29","Mohammed Younus",1,"","D","Medium","they ensure that they deliver it within 7-8 working days","Ordered 18 Mar; undelivered on 29 Mar despite 7-8 day promise; paid online","DUP-03")
ic("208025","2025-03-29","Mohammed Younus",1,"","D","Medium","it's almost the 12 th day","Second post on the same incident (12 days)","DUP-03","duplicate")
ic("207829","2025-03-19","Anonymous",16,"18","SR","Medium","no proper information about the order till date in the help center","Refund for 6 Mar order not received; no order info in help centre","DUP-04")
ic("210226","2025-06-21","Vaishnavi",16,"18","SR","Medium","no proper information about the order till date in the help center","Near-identical to IC-207829 apart from order date; probable copy (counted once)","DUP-04","duplicate")
ic("207000","2025-01-27","Anonymous",16,"13","R","Medium","its already been half of month but I don't received my refund","Cancelled order; refund missing after about two weeks")
ic("209833","2025-06-01","Shruti Sunil Gokhale",14,"","R","High","as of today, I have not yet received the refund","Refund promised 23 May not credited by 1 Jun")
ic("206775","2025-01-13","Nitin Agarwal",20,"","R","Medium","the amount has been deducted but order has not been placed","Paytm debit but no order created")
ic("213221","2025-12-21","Sakshi Thapa",20,"","R","Medium","money has been debited but order is not confirmed","Google Pay debit but order unconfirmed")
ic("213752","2026-01-16","Eesha Sollkar",1,"16","DR","Medium","I have not yet received my parcel","Tracking number cited; paid online; asks status or refund")
ic("206599","2025-01-02","Rahul Paul",16,"","R","Low","I have cancelled a roder but I didn't get refund","Cancelled order; no refund")
ic("207446","2025-02-25","Pilli Sheshukumar",14,"7,19","SR","High","I raised ticket on 15 feb but still not get my money back","Perfume combo incomplete; returned; refund pending about 7 days; ticket 15 Feb")
ic("207164","2025-02-06","Amritha",16,"","R","Low","Refund not credited by my bank account","Refund not credited (no detail)")
ic("206962","2025-01-25","Akshaya Sree",16,"","R","Low","Wallet amount is not refund","Wallet amount not refunded (no detail)")
ic("214317","2026-02-23","Najima Faridul islam",1,"5","D","High","it's showing out for delivery","Ordered 13 Feb, ETA 19 Feb; still 'out for delivery' on 23 Feb; paid")

# legacy (pre-2025): id,date,source,url,author,cat,summary,date_verified
L=[]
def lg(i,d,s,u,au,c,sm,dv="Yes"): L.append((i,d,s,u,au,c,sm,dv))
ICL = """206468|2024-12-25|1|Ordered 15 Dec; still undelivered 25 Dec
206289|2024-12-13|14|Cancelled order; refund missing after 10 days
206263|2024-12-11|3|Shown delivered; no call or parcel
206243|2024-12-10|1|11 days undelivered; wants a human
206215|2024-12-08|1|Due 7 Dec; still undelivered; support automated
206206|2024-12-07|14|Refund pending 7 days
205287|2024-10-26|1|Ordered 19 Oct; due 24 Oct; still waiting
206201|2024-12-07|1|Ordered 29 Nov; delivery date passed
205061|2024-10-19|16|Cancelled 30 Sep; no refund by 19 Oct
204860|2024-10-10|1|Two orders undelivered; second cancelled by company
204036|2024-09-16|1|15 days; order not even shipped
205180|2024-10-24|1|10 days undelivered; no response
203803|2024-09-06|1|Due 2 Sep; undelivered 6 Sep; automated support
204795|2024-10-08|1|Ordered 27 Sep; undelivered 8 Oct; hard to reach support
204694|2024-10-06|1|Order not shipped after a week
203232|2024-08-09|7|Missing product; no phone; email unanswered
202246|2024-06-16|8|Ordered 2 units; received 1
199071|2024-01-13|9|Wrong and missing products; wants return
202950|2024-07-25|1|Shown due 22 Jul; undelivered 25 Jul
203465|2024-08-22|14|Cancelled 12 Aug; no refund after 10 days
202948|2024-07-25|14|Cancelled for address issue; no refund after 10 days
204655|2024-10-05|1|ETA slipped 4 to 8 Oct; cannot contact anyone
198398|2023-12-05|9|Wrong products; ticket closed
198035|2023-11-16|20|Payment debited; no order confirmation
197109|2023-10-03|20|Debited twice; order not approved; 2 months
197759|2023-11-01|16|Refund not received in 30 days
196471|2023-09-06|20|Paid; order not confirmed; no refund
197150|2023-10-04|1|5 days after paid order; no response
195136|2023-07-28|8|10 of 16 items received; pouch missing
194558|2023-07-10|2|Paid; never received
194275|2023-06-29|8|Ordered 14; received 7
194107|2023-06-23|11|Leaked lip balm
194290|2023-06-30|20|Debited; no order confirmation
195845|2023-08-18|20|Debited; no order confirmation
193608|2023-06-05|5|Delivery attempt logged; no call; 5 days
194316|2023-07-01|9|Wrong item
193245|2023-05-22|1|12 days undelivered; no action
192509|2023-04-22|3|Marked delivered; not received (hostel)
192488|2023-04-21|20|Address auto-changed to another city
192419|2023-04-19|1|A week without updates
192265|2023-04-12|2|Paid; not received
191679|2023-03-20|3|Shown delivered; nothing received; auto mail
191476|2023-03-12|7|Paid serum missing; only gift arrived
194178|2023-06-26|7|Free perfumes and items missing
191392|2023-03-10|16|Cancelled after 1 hr; cashback not received
192440|2023-04-20|13|Order cancelled by Smytten; refund missing
191122|2023-03-02|15|Refund Rs 184 on a Rs 771 order
192139|2023-04-08|15|One item delivered; other cancelled; refunded Rs 110 of Rs 385
192322|2023-04-14|16|Cancelled; no money back
193384|2023-05-27|16|Returned order; no refund
189537|2022-12-30|7|Lip scrub missing
191633|2023-03-18|7|Lip balm and scrub missing
187415|2022-11-24|3|Shown delivered; ticket closed as resolved
178742|2022-09-19|9|Different-size products received
173453|2022-06-06|3|Not received; no call before delivery
174096|2022-06-25|8|Ordered 3 bottles; received 1
173901|2022-06-19|9|Totally different box received
173866|2022-06-18|16|Cancelled at door (gift missing); refund awaited
191205|2023-03-04|16|Doorstep cancellation; no refund
173462|2022-06-06|7|Conditioner missing
189596|2023-01-02|1|Due 1 Jan; not received; no contact
173221|2022-05-30|2|Ordered 6 May; nothing after 24 days
173054|2022-05-26|11|Empty box; razor missing
172953|2022-05-23|1|Undelivered past date
172941|2022-05-23|7|Paid item missing; email ignored
172718|2022-05-18|20|Debited; order not placed
172582|2022-05-13|1|Two weeks undelivered
172481|2022-05-10|2|Prepaid kit not received
172342|2022-05-06|7|Face wash and gift items missing
171482|2022-04-03|8|Only some items received
172715|2022-05-18|8|Only one item of three received
172447|2022-05-09|2|Parcel missing
172280|2022-05-04|1|Delayed delivery
174519|2022-07-08|1|Not received by 6 Jul date
173210|2022-05-30|1|Not delivered; care line unanswered
170954|2022-03-14|7|Three products missing
171679|2022-04-09|7|Oil missing
170147|2022-02-12|2|Products not reaching
173253|2022-05-31|2|Products not received
172037|2022-04-23|1|Due date passed
171967|2022-04-19|1|Office delivery not received
173999|2022-06-22|7|Two products missing; wrong item sent"""
for ln in ICL.split("\n"):
    i,d,c,sm = ln.split("|")
    lg("IC-"+i,d,ICN,IC+i,"see URL",int(c),sm)
lg("IC-173453b-dup","2022-08-24",ICN,IC+"176856","pooja shah",3,"Identical text to IC-173453 (counted once)")
lg("IC-198035-dup","2023-11-16",ICN,IC+"198035","Vinu.d",20,"Identical text to IC-195845 (counted once)")
lg("IC-206205-dup","2024-12-07",ICN,IC+"206205","RinoRiyas",14,"Duplicate post of IC-206206 (counted once)")
lg("TP-L1","2024-08-09","Trustpilot",TP+"66b602855be2c1cd159fdae5","Lalitha Premchand",7,"Two products missing from Rs 4,300 order; ticket unanswered (same person/date as IC-203232; counted once)")
lg("TP-L2","2023-09-15","Trustpilot",TP+"6503e701104911cb748d7a75","R K",9,"Completely different products; email support only")
lg("TP-L3","2022-10-20","Trustpilot",TP+"63516a57276a7fd30bd5c878","Shivika",2,"Order of 9 Oct never sent; refund refused")
lg("TP-L4","2022-10-20","Trustpilot",TP+"63513c8e8056669a30a655ef","Ananya Srivastava",2,"Says package never received (low detail)")
lg("AP-L1","2024-12-12",A,AP,"Shreyaagrawal23",9,"Wrong products; ticket answered 'delivered right product'")
lg("AP-L2","2024-07-21",A,AP,"Rashimishra12",1,"3-day ETA became 7+ days; 'consignee will collect from branch'; cancel failed")
lg("AP-L3","2023-09-14",A,AP,"R s soni",7,"Fourth missing-product episode; refunds only after many emails")
lg("AP-L4","2021-11-25",A,AP,"ManveenKaurVeenu",3,"Prepaid order shown delivered while in another city; never received")
for i,d,c,sm,dv in [("qmoultruulp","2023-03-24",4,"Order status 'misrouted'; refund after many requests; second order undelivered","Partial (search-index date)"),
 ("ruutuortuuo","2022-05-22",6,"Order returned to sender without informing customer; 2 months","Partial (search-index date)"),
 ("tlrnlplmllp","2022-05-31",2,"Prepaid orders not delivered","Partial (search-index date)"),
 ("lmlnpntluuo","2022-04-23",1,"15 days; none of the orders delivered; no helpline number","Partial (search-index date)"),
 ("qoqsmqqlllp","2022-05-29",2,"Prepaid shipment never delivered","Partial (search-index date)"),
 ("rmuppqopnuo","2021-09-07",1,"Delivery date pushed from 2 Sep to 7 Sep 2021; no refund","No (date inferred from text)")]:
    lg("MS-L-"+i,d,"MouthShut",MS+i,"MouthShut user",c,sm,dv)
for i,d,au,c,sm,ref in [("VL1","2019-09-11","Rounak Kumar Singh",6,"Returned to shipper then stuck in transit; care silent","package-not-delivered/45347"),
 ("VL2","2020-06-03","Bindu Prahlad",2,"Order due late April not delivered by June; emails stopped","smytten-order-number-not-delivered-yet/72991"),
 ("VL3","2021-04-16","Iva Manna",8,"Two items not delivered; emails unanswered; no care number","products-not-delivered/119289"),
 ("VL4","2021-06-04","Shankar",8,"One item of order undelivered for ~2 months","product-not-delivered/124803"),
 ("VL5","2021-06-12","Ishrat",4,"App shows internal error on order status; prepaid; no reply","package-not-delievered/125676"),
 ("VL6","2021-10-30","Soni Kumari",9,"Package contained completely different products","complaint-about-products-i-ordered-from-smytten/140189"),
 ("VL7","2021-12-06","Sejal Patil",1,"ETA slipped daily; no tracking or contact info","order-not-delivered-gets-delayed-regularly/143179"),
 ("VL8","2021-12-29","Aanchal chhabra",4,"Undelivered; no tracking option; emails unanswered","package-not-delivered/144915")]:
    lg("VX-"+i,d,"Voxya",VX+ref,au,c,sm)

IN_END = D("2026-09-29"); IN_START = D("2025-01-01")
hdr = ["complaint_id","date","year","window","source","source_url","exact_quote_(verbatim,<15 words)","summary_(paraphrase)","problem_category","category_group","secondary_problems","journey_stage","funnel_stage","severity","resolution_status","support_involved","refund_involved","delivery_involved","duplicate_group_id","duplicate_status","template_shared","evidence_strength","date_verified","author_handle"]
rows=[]
for (i,d,s,u,au,c,sec,fl,es,fr,sm,dg,ds,so,dv) in R:
    st = so or STAGE[c]
    secn = "; ".join(CATS[int(x)] for x in sec.split(",")) if sec else ""
    res = "Unknown (Voxya label 'Closed' is not proof of resolution)" if s=="Voxya" else "Unresolved at time of posting"
    rows.append([i,D(d),None,"In-window",s,u,fr,sm,CATS[c],grp(c),secn,JOURNEY[st],st,sev(c,fl),res,
        "Yes" if "S" in fl else "Not stated","Yes" if "R" in fl else "No","Yes" if "D" in fl else "No",dg,ds,"Yes" if "T" in fl else "No",es,dv,au])
for (i,d,s,u,au,c,sm,dv) in L:
    dup = "-dup" in i or i=="TP-L1"
    rows.append([i,D(d),None,"Legacy",s,u,"",sm,CATS[c],grp(c),"",JOURNEY[STAGE[c]],STAGE[c],"Not coded","Not coded","Not coded","Not coded","Not coded",
        "LEG-DUP" if dup else "",("duplicate" if dup else "unique"),"No","Not coded",dv,au])
N=len(rows)+1
wb=Workbook(); ws=wb.active; ws.title="Dataset"
F=Font(name="Arial",size=9); HF=Font(name="Arial",size=9,bold=True,color="FFFFFF"); FILL=PatternFill("solid",fgColor="1F3864")
ws.append(hdr)
for r in rows: ws.append(r)
for c in ws[1]: c.font=HF; c.fill=FILL; c.alignment=Alignment(wrap_text=True,vertical="top")
for ri in range(2,N+1):
    ws.cell(ri,3).value=f"=YEAR(B{ri})"
    ws.cell(ri,2).number_format="yyyy-mm-dd"
    for ci in range(1,len(hdr)+1):
        cell=ws.cell(ri,ci); cell.font=F
        if ci in (6,7,8,11): cell.alignment=Alignment(wrap_text=False,vertical="top")
ws.freeze_panes="B2"; ws.auto_filter.ref=f"A1:{get_column_letter(len(hdr))}{N}"
for ci,w in enumerate([12,11,6,10,20,40,44,52,30,18,30,14,20,10,26,12,10,10,10,11,10,10,22,26],1): ws.column_dimensions[get_column_letter(ci)].width=w
def rng(col): return f"Dataset!${col}$2:${col}${N}"
BF=Font(name="Arial",size=10,bold=True); NF=Font(name="Arial",size=10)
def sheet(name,widths):
    s=wb.create_sheet(name)
    for i,w in enumerate(widths,1): s.column_dimensions[get_column_letter(i)].width=w
    return s
def put(s,r,c,v,bold=False,fmt=None):
    cell=s.cell(r,c); cell.value=v; cell.font=BF if bold else NF
    if fmt: cell.number_format=fmt
    cell.alignment=Alignment(wrap_text=True,vertical="top"); return cell
UQ=f'{rng("T")},"unique"'; INW=f'{rng("D")},"In-window"'
# Category distribution
cd=sheet("Category_Distribution",[38,14,14,12,16,10,10,12,12,12,14])
put(cd,1,1,"Analysis date (as-of)",True); put(cd,1,2,dt.date(2026,9,29),fmt="yyyy-mm-dd")
put(cd,2,1,"Cutoff: last 12 months (>=)"); put(cd,2,2,"=EDATE($B$1,-12)",fmt="yyyy-mm-dd")
put(cd,3,1,"Cutoff: last 6 months (>=)"); put(cd,3,2,"=EDATE($B$1,-6)",fmt="yyyy-mm-dd")
put(cd,4,1,"Cutoff: last 3 months (>=)"); put(cd,4,2,"=EDATE($B$1,-3)",fmt="yyyy-mm-dd")
h=["Problem category","Unique in-window (Jan 2025-Sep 2026)","% of all unique in-window","WISMO core (cat 1-6)?","% within WISMO core","2025","2026","Last 12 mo","Last 6 mo","Last 3 mo","Legacy pre-2025 (unique, separate)"]
for j,x in enumerate(h,1): put(cd,6,j,x,True)
r0=7
for k in range(1,21):
    r=r0+k-1; put(cd,r,1,CATS[k])
    put(cd,r,2,f'=COUNTIFS({rng("I")},$A{r},{INW},{UQ})')
    put(cd,r,3,f'=B{r}/$B${r0+20}',fmt="0.0%")
    put(cd,r,4,"Yes" if k<=6 else "No")
    put(cd,r,5,f'=IF(D{r}="Yes",B{r}/SUMIFS($B${r0}:$B${r0+19},$D${r0}:$D${r0+19},"Yes"),"")',fmt="0.0%")
    put(cd,r,6,f'=COUNTIFS({rng("I")},$A{r},{INW},{UQ},{rng("C")},2025)')
    put(cd,r,7,f'=COUNTIFS({rng("I")},$A{r},{INW},{UQ},{rng("C")},2026)')
    put(cd,r,8,f'=COUNTIFS({rng("I")},$A{r},{INW},{UQ},{rng("B")},">="&$B$2)')
    put(cd,r,9,f'=COUNTIFS({rng("I")},$A{r},{INW},{UQ},{rng("B")},">="&$B$3)')
    put(cd,r,10,f'=COUNTIFS({rng("I")},$A{r},{INW},{UQ},{rng("B")},">="&$B$4)')
    put(cd,r,11,f'=COUNTIFS({rng("I")},$A{r},{rng("D")},"Legacy",{UQ})')
tr=r0+20; put(cd,tr,1,"TOTAL",True)
for c in (2,6,7,8,9,10,11):
    L_=get_column_letter(c); put(cd,tr,c,f"=SUM({L_}{r0}:{L_}{tr-1})",True)
put(cd,tr,3,f"=SUM(C{r0}:C{tr-1})",True,"0.0%")
put(cd,tr+2,1,"Counts are of publicly observable complaints in this dataset, not prevalence among Smytten customers. Each row is one primary category (the failure the user leads with).")
# Funnel
fu=sheet("Funnel",[28,14,14,60])
for j,x in enumerate(["Funnel stage","Unique in-window","% of unique","Note"],1): put(fu,1,j,x,True)
stg=[("Order placed/confirmed","Payment debited/no order, cancellations, address problems"),("Packed/Shipped","Not dispatched after promised date (rarely stated)"),("In transit","Delays, frozen tracking, orders never arriving"),("Out for delivery","Courier attempt failures, wrong numbers, no calls"),("Delivered","Marked delivered but not received"),("Post-delivery","Missing, partial, wrong, leaking/empty items"),("Refund / replacement","Refund delays/non-receipt, partial refunds"),("Support","Support-first complaints")]
for i,(sname,note) in enumerate(stg,2):
    put(fu,i,1,sname); put(fu,i,2,f'=COUNTIFS({rng("M")},$A{i},{INW},{UQ})'); put(fu,i,3,f"=B{i}/$B$10",fmt="0.0%"); put(fu,i,4,note)
put(fu,10,1,"TOTAL",True); put(fu,10,2,"=SUM(B2:B9)",True)
put(fu,12,1,"Stage is inferred from the failure the user leads with; many complaints span several stages (see secondary_problems).")
# Severity
sv=sheet("Severity",[14,16,12,90])
for j,x in enumerate(["Severity","Unique in-window","% of unique","Criteria (defined before assignment; coded from category + support-failure flag)"],1): put(sv,1,j,x,True)
crit={"Low":"Insufficient detail to size impact (one-liners) — applied only where category default is Low (none by default).","Medium":"Delay, tracking, courier-attempt, damage/leak or support friction where item/money may still arrive.","High":"Money or paid item at stake and unresolved: not received, missing/wrong item, refund not received, unilateral cancellation.","Critical":"Marked delivered but not received (money paid, no product, no verified attempt) OR any High item where user reports support failure (closed/ignored/bot loop)."}
for i,sname in enumerate(["Low","Medium","High","Critical"],2):
    put(sv,i,1,sname); put(sv,i,2,f'=COUNTIFS({rng("N")},$A{i},{INW},{UQ})'); put(sv,i,3,f"=B{i}/$B$6",fmt="0.0%"); put(sv,i,4,crit[sname])
put(sv,6,1,"TOTAL",True); put(sv,6,2,"=SUM(B2:B5)",True)
put(sv,8,1,"Severity is a coding of the complaint as written, not a verified loss amount.")
# Sources
so_=sheet("Source_Summary",[30,14,14,14,80])
for j,x in enumerate(["Source","Rows (in-window)","Unique in-window","Legacy rows","Coverage / bias note"],1): put(so_,1,j,x,True)
srcs=[("Trustpilot","All 27 public reviews opened (2 pages). Self-selected; 78% of ratings 1-star; profile claimed by Smytten Apr 2026; mirrors (dk/pt/no/www) are the same reviews."),
("Voxya","Consumer-complaint platform (129 complaints listed). Only complaints whose page/snippet showed date and text were counted; list view not enumerable."),
("Apple App Store","Public reviews page showed 10 reviews of ~134k ratings (4.7 avg); no per-review permalinks."),
("MouthShut","Individual review pages seen via search index; listing page did not render reviews. Date from search metadata."),
("IndiaCustomerCare (comments)","Anonymous/unverified public comments (2 pages, ~150 comments read). Comments can be typed by anyone; templated text seen.")]
for i,(sname,note) in enumerate(srcs,2):
    put(so_,i,1,sname); put(so_,i,2,f'=COUNTIFS({rng("E")},$A{i},{INW})'); put(so_,i,3,f'=COUNTIFS({rng("E")},$A{i},{INW},{UQ})'); put(so_,i,4,f'=COUNTIFS({rng("E")},$A{i},{rng("D")},"Legacy")'); put(so_,i,5,note)
put(so_,7,1,"TOTAL",True)
for c in (2,3,4): put(so_,7,c,f"=SUM({get_column_letter(c)}2:{get_column_letter(c)}6)",True)
nots=[("Google Play","Not sampleable: page lists ~912K reviews but only 3 (all 5-star, text unrelated to shopping) render without login. 0 counted."),
("Reddit","No retrievable first-person Smytten threads via my search tools. 0 counted (absence of results is not absence of posts)."),
("Quora / X (Twitter) / Instagram / Facebook / YouTube","Not retrievable via my tools. 0 counted."),
("ConsumerComplaints.in / ComplaintsBoard / PissedConsumer / Sitejabber","No Smytten pages surfaced in searches. 0 counted."),
("News / blog / case studies (Tier 3)","Not used as complaints; no identifiable underlying user complaints found.")]
for i,(sname,note) in enumerate(nots,9):
    put(so_,i,1,sname); put(so_,i,2,0); put(so_,i,3,0); put(so_,i,4,0); put(so_,i,5,note)
# Overall metrics
om=sheet("Overall_Metrics",[58,16,60])
for j,x in enumerate(["Metric","Value","Definition"],1): put(om,1,j,x,True)
M=[("Rows in dataset (all windows)",f"=COUNTA({rng('A')})","All rows incl. duplicates and legacy"),
("In-window rows (Jan 2025-Sep 2026)",f'=COUNTIFS({INW})',"Rows before de-duplication"),
("In-window duplicate rows",f'=COUNTIFS({INW},{rng("T")},"duplicate")',"Same incident/text posted again (see duplicate_group_id)"),
("In-window UNIQUE complaints",f'=COUNTIFS({INW},{UQ})',"Headline count"),
("Conservative unique (collapse shared-template groups)",f'=B5-(COUNTIFS({INW},{UQ},{rng("U")},"Yes")-3)',"3 template groups (7 rows) collapsed to 1 each"),
("Legacy unique complaints (pre-2025, separate)",f'=COUNTIFS({rng("D")},"Legacy",{UQ})',"Reported separately; not in headline"),
("Distinct sources with counted complaints","=COUNTIF(Source_Summary!C2:C6,\">0\")","Platforms with >=1 unique in-window row"),
("Named (non-anonymous) authors among unique in-window rows",f'=COUNTIFS({INW},{UQ},{rng("X")},"<>Anonymous")',"Proxy for identifiable users (not distinct-verified across sources)"),
("% unique in-window rated High evidence",f'=COUNTIFS({INW},{UQ},{rng("V")},"High")/B5',"Evidence strength coded by me"),
("% unique in-window rated High or Medium evidence",f'=(COUNTIFS({INW},{UQ},{rng("V")},"High")+COUNTIFS({INW},{UQ},{rng("V")},"Medium"))/B5',""),
("% unresolved at time of posting",f'=COUNTIFS({INW},{UQ},{rng("O")},"Unresolved at time of posting")/B5',"Structurally high: people post when unresolved (source bias)"),
("% involving delivery",f'=COUNTIFS({INW},{UQ},{rng("R")},"Yes")/B5',"delivery_involved = Yes"),
("% involving refunds",f'=COUNTIFS({INW},{UQ},{rng("Q")},"Yes")/B5',"refund_involved = Yes"),
("% where user says they contacted support",f'=COUNTIFS({INW},{UQ},{rng("P")},"Yes")/B5',"support_involved = Yes"),
("% WISMO core (categories 1-6)",f'=COUNTIFS({INW},{UQ},{rng("J")},"WISMO core")/B5',"Delivery delay through lost/returned"),
("% with a support-failure flag in category or secondary",f'=(COUNTIFS({INW},{UQ},{rng("I")},"Customer-support*")+COUNTIFS({INW},{UQ},{rng("K")},"*Customer-support*",{rng("I")},"<>Customer-support*"))/B5',"Primary or secondary support problem")]
for i,(m,f,dfn) in enumerate(M,2):
    put(om,i,1,m); c=put(om,i,2,f); put(om,i,3,dfn)
    if m.startswith("%"): c.number_format="0.0%"
put(om,len(M)+3,1,"Prevalence caveat: none of these are rates among Smytten customers; no order-volume denominator is public.")
# Evidence
ev=sheet("Top_Findings_Evidence",[34,12,12,20,50,60])
for j,x in enumerate(["Finding (primary category)","Complaint ID","Date","Source","Verbatim fragment","URL"],1): put(ev,1,j,x,True)
E=[("Marked delivered but not received","TP-09"),("Marked delivered but not received","VX-01"),("Marked delivered but not received","IC-213684"),("Marked delivered but not received","MS-01"),
("Delivery delay / order not received","TP-04"),("Delivery delay / order not received","VX-02"),("Delivery delay / order not received","IC-213885"),("Delivery delay / order not received","AP-02"),
("Wrong item","TP-07"),("Wrong item","TP-05"),("Wrong item","IC-208769"),("Wrong item (legacy, Dec 2024)","AP-L1"),
("Missing / partial items","TP-11"),("Missing / partial items","VX-09"),("Missing / partial items","IC-211778"),("Missing / partial items","AP-05"),
("Refund not received / delayed","VX-06"),("Refund not received / delayed","IC-207000"),("Refund not received / delayed","AP-01"),("Refund not received / delayed","TP-12"),
("Support failure (with an order problem)","TP-07"),("Support failure (with an order problem)","AP-03"),("Support failure (with an order problem)","IC-213366"),("Support failure (with an order problem)","VX-07"),
("Cancellation problems","TP-10"),("Cancellation problems","AP-02"),("Cancellation problems","IC-213013"),("Cancellation problems","VX-06")]
for i,(f,cid) in enumerate(E,2):
    put(ev,i,1,f); put(ev,i,2,cid)
    put(ev,i,3,f'=INDEX({rng("B")},MATCH($B{i},{rng("A")},0))',fmt="yyyy-mm-dd")
    put(ev,i,4,f'=INDEX({rng("E")},MATCH($B{i},{rng("A")},0))')
    put(ev,i,5,f'=INDEX({rng("G")},MATCH($B{i},{rng("A")},0))')
    put(ev,i,6,f'=INDEX({rng("F")},MATCH($B{i},{rng("A")},0))')
# Excluded
ex=sheet("Excluded_or_Uncounted",[30,16,90])
for j,x in enumerate(["Item","Date","Reason not counted"],1): put(ex,1,j,x,True)
X=[("Trustpilot: Asmita Biswas","2025-12-08","Says support is unhelpful for an order but states no specific problem"),
("Trustpilot: Sagar","2025-05-23","Alleges unordered COD parcels attributed to Smytten; not a failure on a placed order; attribution unverifiable"),
("Trustpilot: 6 five-star reviews","2024-2026","Positive experiences (incl. on-time delivery reports) - excluded per scope"),
("Trustpilot: dk/pt/no/www copies","n/a","Locale mirrors of the same reviews - counted once"),
("Voxya: Pavitra (VX-05)","2025-12-26","Duplicate text of VX-04 (DUP-01)"),
("Voxya: 'Refund not processed' (id 242368) and other listing-only hits","various","Search snippet did not show the complaint's own text/date; not opened"),
("IndiaCustomerCare: 30 Dec 2024 (number change), 10 Jan 2025 and 5 Dec 2025 ('Did you get your refund?'), 6 Jan 2026 ('same thing'), 30 Jan 2025 ('Refund money'), 27 Jan 2025 (order-detail query)","2024-2026","Questions, replies or one-word posts with no specific problem"),
("IndiaCustomerCare: cancel-request-only and change-of-mind posts (2022-2023)","2022-2023","No fulfilment failure stated"),
("Apple: 'Positive, but hidden problem' shown twice on page","2026-04-04","Same review rendered twice - counted once"),
("Google Play reviews","n/a","Not accessible in bulk; 3 visible reviews were 5-star and off-topic"),
("MouthShut listing page","n/a","Review list did not render; only individually indexed reviews used"),
("Reddit / Quora / X / Instagram","n/a","Not retrievable via available tools"),
("Smytten replies on app stores","n/a","Company responses are not user complaints")]
for i,(a_,b_,c_) in enumerate(X,2): put(ex,i,1,a_); put(ex,i,2,b_); put(ex,i,3,c_)
# README
rd=wb.create_sheet("README",0); rd.column_dimensions["A"].width=130
T_=["Smytten post-purchase (WISMO + adjacent) complaint dataset - research pass as of 2026-09-29",
"WHAT THIS IS: Publicly visible first-person complaints located with web search/fetch tools. It is NOT a census and NOT a prevalence estimate.",
"HEADLINE: see Overall_Metrics (in-window unique count). Target of 1,000+ was NOT reached; the count is what was independently verifiable with available tools.",
"WINDOW: in-window = 2025-01-01 to 2026-09-29. Legacy (pre-2025) rows are kept separate and excluded from headline statistics.",
"EVIDENCE RULE: a row counts only if a permalink/page, a date, and the user's own words describing a specific post-order problem were seen. Google Play, Reddit, Quora, X could not be sampled.",
"QUOTES: exact_quote is a verbatim fragment under 15 words (copyright/quoting limits); summary is my paraphrase. Full text is at source_url.",
"CATEGORY RULE: exactly one primary category = the failure the user leads with; secondary_problems lists others. Refund delay = user states wait of 10 days or less; refund not received = longer or 'not credited'.",
"DELAY vs NOT RECEIVED: Delivery delay = past promised date and under ~3 weeks; Order not received = 3+ weeks, or user says it never arrived.",
"DEDUPLICATION: duplicate_status='duplicate' rows are excluded from unique counts (same incident or identical text). template_shared='Yes' marks identical wording posted under different names/order IDs; kept as separate incidents but flagged (see conservative count).",
"DATES: Trustpilot = published date shown (experience date can differ). Apple 'd Mon' dates have no year; 2026 inferred from Apple's format and version history (flagged Partial). MouthShut dates come from search-index metadata.",
"SEVERITY: coded from category plus a support-failure flag (see Severity sheet). Not a verified loss amount.",
"RESOLUTION: 'Unresolved at time of posting' reflects the post only; later resolution is unknown. Complaint venues over-represent unresolved cases.",
"BIAS: Trustpilot/Voxya/IndiaCustomerCare attract dissatisfied users; comments on IndiaCustomerCare are unverified and partly templated; nothing here supports a claim about the share of all Smytten customers affected.",
"Company claims (not verified here): Smytten describes itself as serving 30M+ users (Trustpilot profile text); no order-volume or failure-rate denominator is public."]
for i,t in enumerate(T_,1):
    c=rd.cell(i,1); c.value=t; c.font=Font(name="Arial",size=11 if i>1 else 13,bold=(i==1)); c.alignment=Alignment(wrap_text=True,vertical="top")
wb.save("/home/claude/smytten_wismo_complaints_dataset.xlsx")
print("rows",len(rows),"N",N)