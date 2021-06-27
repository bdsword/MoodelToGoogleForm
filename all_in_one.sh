#!/bin/bash

BUILD_DIR="build"
META_PATH="$BUILD_DIR/meta.csv"
HTML_PATH="$BUILD_DIR/questions.html"
IMAGES_PATH="$BUILD_DIR/images"

if [ "$#" -ne "1" ]; then
    echo -e "Usage:\n$0 <question dir>"
    exit 1
fi
QUESTION_DIR="$1"

if [ -d $BUILD_DIR ]; then
    rm -rf $BUILD_DIR
fi

echo -e "Create build directory..."
mkdir $BUILD_DIR
mkdir $IMAGES_PATH

echo -e "Running parse_moodle.py..."
./parse_moodle.py --meta_csv_path ${META_PATH} --html_path ${HTML_PATH} ${QUESTION_DIR}

echo -e "Running html_to_imgs.py..."
./html_to_imgs.py --output_dir ${IMAGES_PATH} ${HTML_PATH} 

echo -e "Running generate_google_form.py..."
./generate_google_form.py --meta_csv_path ${META_PATH} --images_dir_path ${IMAGES_PATH}
