#!/home/sunnymarkliu/software/miniconda2/bin/python
# _*_ coding: utf-8 _*_

"""
@author: MarkLiu
@time  : 17-3-6 上午11:38
"""
import h5py
import numpy as np
import progressbar as pbar
from PIL import Image
from tensorflow.examples.tutorials.mnist import input_data
import sys

import utils

imagenet_mean = {'R': np.float16(103.939), 'G': np.float16(116.779), 'B': np.float16(123.68)}


class DataWapper(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.pointer = 0
        self.total_count = self.x.shape[0]

    def shuffle(self):
        shuffled_index = np.arange(0, self.total_count)
        np.random.shuffle(shuffled_index)
        self.x = self.x[shuffled_index]
        self.y = self.y[shuffled_index]

    def next_batch(self, batch_size):
        end = self.pointer + batch_size
        if end > self.total_count:
            end = self.total_count

        batch_x = self.x[self.pointer: end]
        batch_y = self.y[self.pointer: end]

        self.pointer = end

        if self.pointer == self.total_count:
            self.shuffle()
            self.pointer = 0

        return batch_x, batch_y


class ImageDataTransfer(object):
    def __init__(self, pre_img_rows, pre_img_cols, pre_images, output_rows, output_cols):
        self.pre_img_rows = pre_img_rows
        self.pre_img_cols = pre_img_cols
        self.pre_images = pre_images
        self.output_rows = output_rows
        self.output_cols = output_cols

    def transfer(self):
        image_reshape = np.ndarray(shape=(self.pre_images.shape[0], self.output_rows, self.output_cols, 3),
                                   dtype=np.float16)

        widgets = ['Transfer: ', pbar.Percentage(), ' ', pbar.Bar('>'), ' ', pbar.ETA()]
        image_bar = pbar.ProgressBar(widgets=widgets, maxval=self.pre_images.shape[0]).start()

        for i in range(0, self.pre_images.shape[0]):
            image = self.pre_images[i].reshape(self.pre_img_rows, self.pre_img_cols)
            image = image.astype('uint8')
            im = Image.fromarray(image)  # monochromatic image
            imrgb = im.convert('RGB')
            imrgb = imrgb.resize((self.output_rows, self.output_cols), Image.ANTIALIAS)

            im = np.array(imrgb, dtype=np.float16)
            im[:, :, 0] -= imagenet_mean['R']
            im[:, :, 1] -= imagenet_mean['G']
            im[:, :, 2] -= imagenet_mean['B']
            # 'RGB'->'BGR', historical reasons in OpenCV
            im = im[:, :, ::-1]
            image_reshape[i] = im

            # test for correct convert!
            # if i < 3:
            #     img = Image.fromarray(np.uint8(im))
            #     img.save(str(i) + '.jpeg', 'jpeg')
            image_bar.update(i + 1)
        image_bar.finish()
        print('image_reshape:', image_reshape.shape)

        return image_reshape


def mnist_reshape(target='alexnet'):
    """
    mnist 数据集进行reshape, target: alexnet、vggnet
    """
    print('transform mnist data to ' + target + ' model size...')
    # translate mnist -> alexnet model, vgg_net model
    mnist = input_data.read_data_sets(utils.mnist_dir, one_hot=True)
    images = mnist.train.images * 255
    labels = mnist.train.labels

    target_train_file = utils.train_mnist_2_imagenet_size_file
    target_test_file = utils.test_mnist_2_imagenet_size_file
    output_rows = 227
    output_cols = 227
    if target == 'vggnet':
        output_rows = 224
        output_cols = 224
        target_train_file = utils.train_mnist_2_vggnet_size_file
        target_test_file = utils.test_mnist_2_vggnet_size_file

    image_transfer = ImageDataTransfer(28, 28, images, output_rows, output_cols)
    images_reshape = image_transfer.transfer()
    try:
        with h5py.File(target_train_file, 'w') as f:
            f.create_dataset('images', data=images_reshape)
            f.create_dataset('labels', data=labels)
            print('Save transformed images to ' + target_train_file)
    except Exception as e:
        print('Unable to save images:', e)

    images = mnist.test.images * 255
    labels = mnist.test.labels
    image_transfer = ImageDataTransfer(28, 28, images, output_rows, output_cols)
    images_reshape = image_transfer.transfer()
    try:
        with h5py.File(target_test_file, 'w') as f:
            f.create_dataset('images', data=images_reshape)
            f.create_dataset('labels', data=labels)
            print('Save transformed images to ' + target_test_file)
    except Exception as e:
        print('Unable to save images:', e)


def main():
    target = 'vggnet'
    if len(sys.argv) > 1:
        target = sys.argv[1]
    mnist_reshape(target)

if __name__ == '__main__':
    main()
