import argparse
from models.AnimeGAN.tools.utils import *
import os
from tqdm import tqdm
from glob import glob
import time
import numpy as np
from models.AnimeGAN.net import generator
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

def parse_args():
    desc = "AnimeGAN"
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--checkpoint_dir', type=str, default='checkpoint/'+'generator_Hayao_weight/',
                        help='Directory name to save the checkpoints')
    parser.add_argument('--test_dir', type=str, default='dataset/test/HR_photo',
                        help='Directory name of test photos')
    parser.add_argument('--style_name', type=str, default='Hayao',
                        help='what style you want to get')
    parser.add_argument('--if_adjust_brightness', type=bool, default=False,
                        help='adjust brightness by the real photo')

    return parser.parse_args()

def stats_graph(graph):
    flops = tf.profiler.profile(graph, options=tf.profiler.ProfileOptionBuilder.float_operation())
    # params = tf.profiler.profile(graph, options=tf.profiler.ProfileOptionBuilder.trainable_variables_parameter())
    print('FLOPs: {}'.format(flops.total_float_ops))

def test(checkpoint_dir, style_name, test_dir, if_adjust_brightness, img_size=[256,256]):
    # tf.reset_default_graph()
    test_files = glob('{}/*.*'.format(test_dir))

    result_dir = 'results/'+style_name
    check_folder(result_dir)

    # test_real = tf.placeholder(tf.float32, [1, 256, 256, 3], name='test')
    test_real = tf.placeholder(tf.float32, [1, None, None, 3], name='test')

    with tf.variable_scope("generator", reuse=False):
        test_generated = generator.G_net(test_real).fake

    generator_var = [var for var in tf.trainable_variables() if var.name.startswith('generator')]
    saver = tf.train.Saver(generator_var)

    gpu_options = tf.GPUOptions(allow_growth=True)
    with tf.Session(config=tf.ConfigProto(allow_soft_placement=True, gpu_options=gpu_options)) as sess:
        # tf.global_variables_initializer().run()
        # load model
        ckpt = tf.train.get_checkpoint_state(checkpoint_dir)  # checkpoint file information
        if ckpt and ckpt.model_checkpoint_path:
            ckpt_name = os.path.basename(ckpt.model_checkpoint_path)  # first line
            saver.restore(sess, os.path.join(checkpoint_dir, ckpt_name))
            print(" [*] Success to read {}".format(ckpt_name))
        else:
            print(" [*] Failed to find a checkpoint")
            return
        
        # FLOPs
        # stats_graph(tf.get_default_graph())

        begin = time.time()
        for sample_file  in tqdm(test_files) :
            # print('Processing image: ' + sample_file)
            sample_image = np.asarray(load_test_data(sample_file, img_size))
            image_path = os.path.join(result_dir,'{0}'.format(os.path.basename(sample_file)))
            fake_img = sess.run(test_generated, feed_dict = {test_real : sample_image})
            if if_adjust_brightness:
                save_images(fake_img, image_path, sample_file)
            else:
                save_images(fake_img, image_path, None)
        end = time.time()
        print(f'test-time: {end-begin} s')
        print(f'one image test time : {(end-begin)/len(test_files)} s')
        print(f'result path: {result_dir}')
if __name__ == '__main__':
    arg = parse_args()
    print(arg.checkpoint_dir)
    test(arg.checkpoint_dir, arg.style_name, arg.test_dir, arg.if_adjust_brightness)
