'''Takes a static image and creates a short Ken Burns effect video'''

import os
from PIL import Image
import subprocess



im = Image.open('img/paper.jpg')
image_width = im.size[0]
image_height = im.size[1]
ratio = image_height/image_width
my_box_dim = [int(300/ratio), 300]

initial_width = int(image_width*.05)
initial_height = int(image_height*.05)

box = [initial_width, initial_height, (my_box_dim[0]+initial_width), (my_box_dim[1]+initial_height)]

full_speed = int(min(image_height, image_width)/100)

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
    box[0] = box[0] + int(full_speed * v)
    box[1] = box[1] + int(full_speed * v)
    box[2] = box[2] + int(full_speed * v)
    box[3] = box[3] + int(full_speed * v)
    frame = im.resize(my_box_dim, box=box)
    frame.save(name, format='png')
    i += 1
    my_frames.append(frame)

decel_speed = accel_speed
decel_speed.reverse()

for _ in range(50):
    name = ('temp/' + ('%0*d' % (3, i)) + '.png')
    box[0] = box[0] + full_speed
    box[1] = box[1] + full_speed
    box[2] = box[2] + full_speed
    box[3] = box[3] + full_speed
    frame = im.resize(my_box_dim, box=box)
    frame.save(name, format='png')
    i += 1
    my_frames.append(frame)

for v in decel_speed:
    name = ('temp/' + ('%0*d' % (3, i)) + '.png')
    box[0] = box[0] + int(full_speed * v)
    box[1] = box[1] + int(full_speed * v)
    box[2] = box[2] + int(full_speed * v)
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
