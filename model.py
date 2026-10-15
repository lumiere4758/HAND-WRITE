import numpy as np
from PIL import Image
import utils

class handwritingTranslator(object):
    def __init__(self, model=1):
        self.M_SIZE = 28
        self.PADDING = 8
        self.MAP_SYMBOLS = {'+': 10, '-': 11, 'x': 12, '/':13, '(':14, ')':15, ',':16}
        if model == 1:
            import keras
            self.model = keras.models.load_model('model.h5')

    def image_centering(self, img):
        # return m_size x m_size array of img on center with padding
        cx,cy = utils.find_image_center(img)
        p = int(self.M_SIZE /2)
        img = np.pad(img, ((p,p),(p,p)), 'constant')
        cx += p
        cy += p
        img = img[cy-p:cy+p, cx-p:cx+p]
        return img

    def image_resize(self, img):
        # resize image keep aspect ratio to MNIST sample scale
        h, w = img.shape
        if h == max(h, w):
            h1 = self.M_SIZE - self.PADDING
            w1 = round((h1/h)*w)
        else:
            w1 = self.M_SIZE - self.PADDING
            h1 = round((w1/w)*h)

        # image for Image object, img for array object
        image = Image.fromarray(np.uint8(img), 'L')
        image = image.resize((w1, h1))
        img = np.array(image)
        return img
    def crop(self, img, label):
        # crop image based on label
        thresh = np.vectorize(lambda x: 1 if x == label else 0)
        img = thresh(img)
        cx, cy = utils.find_image_center(img)
        v,h = np.nonzero(img)
        img = img[min(v): max(v)+1, min(h): max(h)+1]
        return img, cx

    def detect(self, img):
        # detect n separate image of symbols from image
        # b row connected components algorithm
        # return list of image and label
        d = {0:0}
        idx = 0
        for i in range(img.shape[0]):
            for j in range(img.shape[1]):
                if img[i,j] != 0:
                    top = img[i-1, j]
                    left = img[i, j-1]
                    if (left != 0 and (top ==0 or top == left)):
                        img[i,j] = left
                    elif ((left == 0 or left == top) and top != 0):
                        img[i,j] = top
                    elif left != 0 and top != 0 and left != top:
                        img[i,j] = min(left, top)
                        d[max(left, top)] = min(left,top)
                    else:
                        idx += 1
                        img[i,j] = idx
                        d[idx] = idx
        d = utils.clean_equivalency_dict(d)
        map_d = np.vectorize(d.get)
        imgs = map_d(img)
        return imgs, d

    def thresholding(self, image):
        # convert image object to numpy array
        img = np.array(image)
        #then threshofling each pixel to binary(grayscale)
        thresh = np.vectorize(lambda x : 1 if x == 0 else 0)
        img = thresh(img)
        return img

    def predict(self, img):
        # run model.predict from keras model and interpret its symbol
        res = self.model.predict(img.reshape(1, self.M_SIZE**2))
        num = res.argmax()
        conf = round(res.max()*100,2)
        if num>=10:
            num = self.MAP_SYMBOLS[num]
        num = str(num)
        return num, conf

    def calculate(self, calculation):
        # return text contain calculation and answer 
        try :
            result = eval(calculation)
            if calculation == str(result):
                result = ''
            else:
                if int(result) == result:
                    result = int(result)
                else:
                    result = np.round(result, 2)
                result = '=' + str(result)
        except Exception as e:
            result = ''
        result = ' ' + calculation + result
        return result

    def translate(self, image):
        nums = []
        confs = []
        imgs_ok = []
        cxs = []
        imgs = self.thresholding(image)
        imgs, d = self.detect(imgs)
        labels = set(d.values())
        labels.remove(0)
        for label in sorted(labels):
            img, cx = self.crop(imgs, label)
            img = self.image_resize(img)
            img = self.image_centering(img)
            num, conf = self.predict(img)
            nums.append(num)
            confs.append(conf)
            nums.append(num)
            confs.append(conf)
            imgs_ok.append(img)
            cxs.append(cx)
        nums = utils.sort_by_other_list(nums, cxs)
        confs = utils.sort_by_other_list(confs, cxs)
        imgs_ok = utils.sort_by_other_list(imgs_ok, cxs)
        calculation = ''.join(nums)
        display = self.calculate(calculation)
        return display

    def prep(self, image):
        # prepare single image to be formatted like MNIST sample image
        img = self.thresholding(image)
        img, cx = self.crop(img, 1)
        img = self.image_resize(img)
        img = self.image_centering(img)
        return img


        