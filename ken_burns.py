'''Takes a static image and creates a short Ken Burns effect video'''

import os
from PIL import Image
import subprocess

my_box_dim = [300, 300]

im = Image.open('img/paper.jpg')

box = [50, 50, (my_box_dim[0]+50), (my_box_dim[1]+50)]

full_speed = 10

accel_speed = [0.05, 0.05, 0.05, 0.05, 0.05, 0.05,
               0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
               0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
               0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
               0.2, 0.2, 0.2,
               0.3, 0.3, 0.3, 0.3, 0.3, 0.3,
               0.4, 0.4, 0.4, 0.4, 0.4, 0.4,
               0.5, 0.5, 0.5,
               0.6, 0.6, 0.6,
               0.8, 0.8,
               0.9, 0.9]


def create_gif(frames_list):
    frames_list[0].save('temp/temp.gif',
                        save_all=True,
                        append_images=frames_list[1:],
                        loop=1,
                        minimize_size=True,
                        allow_mixed=True)


my_frames = []
i = 1
for v in accel_speed:
    name = ('temp/' + ('%0*d' % (3, i)) + '.png')
    box[0] = box[0] + 2
    box[1] = box[1] + int(full_speed * v)
    box[2] = box[2] + 2
    box[3] = box[3] + int(full_speed * v)
    frame = im.resize(my_box_dim, box=box)
    frame.save(name, format='png')
    i += 1
    my_frames.append(frame)

decel_speed = accel_speed
decel_speed.reverse()

for _ in range(50):
    name = ('temp/' + ('%0*d' % (3, i)) + '.png')
    box[0] = box[0] + 2
    box[1] = box[1] + int(full_speed * v)
    box[2] = box[2] + 2
    box[3] = box[3] + int(full_speed * v)
    frame = im.resize(my_box_dim, box=box)
    frame.save(name, format='png')
    i += 1
    my_frames.append(frame)

for v in decel_speed:
    name = ('temp/' + ('%0*d' % (3, i)) + '.png')
    box[0] = box[0] + 2
    box[1] = box[1] + int(full_speed * v)
    box[2] = box[2] + 2
    box[3] = box[3] + int(full_speed * v)
    frame = im.resize(my_box_dim, box=box)
    frame.save(name, format='png')
    i += 1
    my_frames.append(frame)

create_gif(my_frames)
my_movie_path = 'temp/temp.mp4'
if os.path.isfile(my_movie_path):
    os.remove(my_movie_path)

# For some reason this script won't run in Pycharm
cmd = subprocess.Popen(['bash', 'shell_scripts/make_movie.sh'])
