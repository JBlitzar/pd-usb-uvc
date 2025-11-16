cd "$(dirname "$0")"
rm /Volumes/CIRCUITPY/*.bin # clear up space before copying over
cp pd-src/*.py /Volumes/CIRCUITPY/
cp pd-src/*.bin /Volumes/CIRCUITPY/