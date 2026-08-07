Install the optional Python packages `face_recognition` and `numpy` in the Odoo
environment for face detection to work. Without them the module still installs, but
images are flagged with a _scan error_ state and no faces are detected.

Assign the _Face Manager_ group to users who should manage people and faces. Regular
users can view detected faces and identify them through the wizards.

Under _Settings \> General Settings \> LensMemoriae \> Automatic Face Detection_ you can:

- Toggle the scheduled face scan and suggestion crons on/off.
- Tune the batch size of images processed per scan run and the number of faces
  evaluated per suggestion run.
