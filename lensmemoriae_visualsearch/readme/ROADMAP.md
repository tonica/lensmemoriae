- Detect rotated or mirrored crops (currently only axis-aligned crops are recognised;
  this would need feature matching such as OpenCV/ORB)
- Make the search query scale-invariant across the whole image so larger/smaller
  versions of the same photo match with looser thresholds
- Optimise the similarity scan in SQL (bitwise operators on the stored hashes) instead
  of in Python to support very large archives
- Distinguish exact-duplicate hits from loose regional matches in the results UI
- Persist a visual-search history per user