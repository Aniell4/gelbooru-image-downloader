#!/usr/bin/env python3

import argparse
import asyncio
import json
import os
import shutil
import stat

import appdirs
from pygelbooru import Gelbooru
import requests

def main():
    parser = argparse.ArgumentParser(description='Downloads all posts with a given set of tags from Gelbooru')
    parser.add_argument('-k', '--api-key', help='Your API key from https://gelbooru.com/index.php?page=account&s=options')
    parser.add_argument('-u', '--user-id', help='Your user ID from https://gelbooru.com/index.php?page=account&s=options')
    parser.add_argument('-n', '--num-images', type=int, default=0, help='The number of images to download')
    parser.add_argument('-s', '--save-credentials', action='store_true', help='Save the provided credentials')
    parser.add_argument('-t', '--save-tags', action='store_true', help='Save the tags associated with each image')
    parser.add_argument('-i', '--index-tags', const='symlink', nargs='?', choices=['symlink', 'hardlink', 'copy'], help='Create a folder for each tag with each relevant image symlinked inside it. By default, files are symlinked.')
    parser.add_argument('-o', '--output', default=os.curdir, help='The directory to save the downloaded posts to')
    parser.add_argument('-b', '--blacklist', nargs='*', help='Tags you do not want in the posts that will be downloaded')
    parser.add_argument('tags', nargs='+', help='Tags you want in the posts that will be downloaded')

    args = parser.parse_args()

    # read saved credentials if they exist
    save_file = os.path.join(appdirs.user_config_dir(), '.gelbooru_creds.json')
    if os.path.exists(save_file):
        with open(save_file, 'r') as file:
            try:
                save_data = json.load(file)
            except json.decoder.JSONDecodeError:
                save_data = {}
    else:
        save_data = {}

    # fall back to saved credentials if none are provided on the command line
    api_key = args.api_key or save_data.get('api_key')
    user_id = args.user_id or save_data.get('user_id')

    # save the credentials if we're asked to save them
    if args.save_credentials:
        if api_key:
            save_data['api_key'] = api_key
        if user_id:
            save_data['user_id'] = user_id

        with open(save_file, 'w') as file:
            # mark the file as only accessible by the user
            os.chmod(save_file, stat.S_IRUSR | stat.S_IWUSR)
            json.dump(save_data, file)

    if api_key is None or user_id is None:
        print('Missing credentials. You must specify both an api key and a user id or have them already saved')

    file_tag_map = download(api_key, user_id, args.output, args.tags, args.blacklist, args.num_images, args.save_tags)
    if args.index_tags:
        index_posts(args.output, file_tag_map, args.index_tags)

def download(api_key: str, user_id: str, save_dir: str, tags: list[str], blacklist_tags: list[str], num_images: int, save_tags: bool):
    if num_images <= 0:
        num_images = 1000
        all_images = True
    else:
        all_images = False

    file_tag_map = {}

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    print('Downloading posts')
    page_num = 0
    num_per_page = min(1000, num_images)
    total = 0
    gelbooru = Gelbooru(api_key, user_id)
    while all_images or total < num_images:
        images = asyncio.run(gelbooru.search_posts(tags=tags, exclude_tags=blacklist_tags, limit=num_per_page, page=page_num))
        if not isinstance(images, list):
            images = [images]
        if len(images) == 0:
            break

        for image in images:
            url = image.file_url
            filename = image.filename
            total += 1
            if all_images:
                print(f'[{total}] ', end='')
            else:
                print(f'[{total}/{num_images}] ', end='')

            response = requests.get(url, stream=True)
            if response.ok:
                file_path = os.path.join(save_dir, filename)
                if not os.path.exists(file_path):
                    with open(file_path, 'wb') as file:
                        # Use 1MB blocks
                        for block in response.iter_content(16*1024*1024):
                            if not block:
                                break
                            file.write(block)
                    print(f'Post sucessfully downloaded: {filename}')

                    file_tag_map[file_path] = image.tags
                else:
                    print(f'Post already downloaded: {filename}')

                if save_tags:
                    tag_file = f'{file_path}.tags'
                    if not os.path.exists(tag_file):
                        with open(tag_file, 'w') as file:
                            file.write('\n'.join(image.tags))
            else:
                print(f'Post could not be retreived: {filename}')

        page_num += 1

    print('Finished downloading all images')

    return file_tag_map

def index_posts(save_dir: str, file_tag_map: dict[str, list[str]], link_mode: str):
    print('Indexing files')
    for file, tags in file_tag_map.items():
        for tag in tags:
            tag_dir = os.path.join(save_dir, tag)
            src_file = os.path.relpath(file, start=tag_dir)
            if not os.path.exists(tag_dir):
                try:
                    os.makedirs(tag_dir)
                except Error:
                    # ignore tags that have illegal characters for file names
                    continue

                tag_dir_file = os.path.join(tag_dir, os.path.basename(file))
                if os.path.exists(tag_dir_file):
                    os.unlink(tag_dir_file)

                if link_mode == 'symlink':
                    os.symlink(src_file, tag_dir_file)
                elif link_mode == 'hardlink':
                    os.link(src_file, tag_dir_file)
                elif link_mode == 'copy':
                    shutil.copy(src_file, tag_dir_file)
                else:
                    raise Exception(f'Unknown link mode: {link_mode}')

    print('File indexing complete')

if __name__ == '__main__':
    main()
