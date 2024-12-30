import cv2
import os

ROOT = os.path.dirname(os.path.realpath(__file__))

if os.name == 'nt':
    FACES = ROOT + '\\faces'
    TRAIN = ROOT + '\\train'
    IMAGES = ROOT + '\\download'
else:
    FACES = ROOT + '/faces'
    TRAIN = ROOT + '/train'
    IMAGES = ROOT + '/download'
    
def detect(srcdir=IMAGES, tgtdir=FACES, traindir=TRAIN):
    for fname in os.listdir(srcdir):
        if not fname.upper().endswith('.JPEG'):
            continue
        fullname = os.path.join(srcdir, fname)
        newname = os.path.join(tgtdir, fname)
        img = cv2.imread(fullname)
        if img is None:
            continue
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        training = os.path.join(traindir, 'haarcascade_frontalface_alt.xml')
        cascade = cv2.CascadeClassifier(training)
        rects = cascade.detectMultiScale(gray, 1.3, 5)
        try:
            if rects.any():
                print('Rosto encontrado')
                rects[:, 2:] += rects[:, :2]
        except AttributeError:
            print(f'Nenhum rosto encontrado em {fname}')
            continue
        
        for x1, y1, x2, y2 in rects:
            cv2.rectangle(img, (x1, y1), (x2, y2), (127, 255, 0), 2)
        cv2.imwrite(newname, img)
        
if __name__ == '__main__':
    detect()
    

    