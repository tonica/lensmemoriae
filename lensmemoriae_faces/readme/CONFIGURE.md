Install the optional Python packages `face_recognition` and `numpy` in the Odoo
environment for face detection to work. Without them the module still installs, but
images are flagged with a _scan error_ state and no faces are detected.

Assign the _Face Manager_ group to users who should manage people and faces. Regular
users can view detected faces and identify them through the wizards.
