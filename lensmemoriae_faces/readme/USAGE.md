Faces are detected automatically by a cron job (by default every 5 minutes, processing
a configurable batch of images). Moderators can also scan a single image from its form
with the _Scan for Faces_ button.

Face scanning and person suggestion crons can be enabled or disabled together from the
settings under _Settings \> General Settings \> LensMemoriae \> Automatic Face Detection_.
When disabled, the scheduled jobs stop running but the manual _Scan for Faces_ button
keeps working.

Images can be excluded from the scan (for example very degraded negatives) with the
_Exclude from Face Scan_ button on the image form, or by setting the exclusion flag
while editing. Excluded images are skipped by the cron and shown with a muted _Excluded_
state.

To use LensMemoriae Faces:

1.  Go to _LensMemoriae \> Faces_ to review detected faces. Use _Identify_, _Accept_ (on
    suggestions), _Ignore_ or _Clear Suggestion_ on each face.
2.  Go to _LensMemoriae \> Suggestions_ to review the faces that the suggestion engine
    matched to a person.
3.  Go to _LensMemoriae \> People_ to manage identified persons: link a partner, review
    reference faces, browse their photos with _View Photos_, or use _Find Matches_ to
    search the whole collection for more images of that person.
4.  On an image form, the _Detected People_ group lists the faces found in that image
    with the same actions as the _Faces_ list.

Filter images with faces from the _Images_ screen using the _Has Faces_ / _No Faces_ /
_Has Identified_ filters, or the _Excluded from Face Scan_ filter to review exclusions.