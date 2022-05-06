import asyncio
import os
import requests
from pygelbooru import Gelbooru

def get_images(tag_list: list[str], num_images: int, page: int):
    gelbooru = Gelbooru('API_KEY', 'USER_ID')
    return asyncio.run(gelbooru.search_posts(tags=tag_list, limit=num_images, page=page))

def main():
    tags = input("Enter Gelbooru Tags: ")
    tag_list = tags.split(' ')
    num_images = int(input('Enter the number of images to download: '))
    download(tags, tag_list, num_images)

def download(save_dir: str, tag_list: list[str], num_images: int):
    if num_images <= 0:
        num_images = 1000
        all_images = True
    else:
        all_images = False

    page_num = 0
    num_per_page = min(1000, num_images)
    total = 0
    while all_images or total < num_images:
        images = get_images(tag_list, num_per_page, page_num)
        if not isinstance(images, list):
            images = [images]
        if len(images) == 0:
            return

        for image in images:
            url = image.file_url
            filename = image.filename
            total += 1
            print(f'[{total}] ', end='')

            response = requests.get(url, stream=True)
            if response.ok:
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                file_path = os.path.join(save_dir, filename)
                if not os.path.exists(file_path):
                    with open(file_path, 'wb') as f:
                        for block in response.iter_content(8192):
                            if not block:
                                break
                            f.write(block)
                    print(f'Image sucessfully downloaded: {filename}')
                else:
                    print(f'Image already downloaded: {filename}')

                tag_file = f'{file_path}.tags'
                if not os.path.exists(tag_file):
                    with open(tag_file, 'w') as f:
                        f.write('\n'.join(image.tags))
            else:
                print(f'Image could not be retreived: {filename}')

        page_num += 1

if __name__ == '__main__':
    main()
