import tkinter
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from functools import partial
import os
import shutil
import re

root = Tk()
root.title('Filename Playlist Maker')
root.resizable(False, False)

prefix_regex = r'^(\[[0-9]{4}\])'  # f'[{4_digit_index}] {filename}'
prefix_length = 7


class Editor:
    def __init__(self, title, working_on_existing_folder: bool = False, remove_prefixes: bool = False):
        self.save = tkinter.BooleanVar()  # True if user clicked 'save changes'
        self.title = title
        self.editor_window = None

        if working_on_existing_folder:
            self.source_directory = filedialog.askdirectory(title='Select Folder')
            # list all files in selected directory
            self.files = [f for f in os.listdir(self.source_directory) if os.path.isfile(
                os.path.join(self.source_directory, f))]
        else:
            self.files = [f for f in filedialog.askopenfilenames(title='Select Files')]
            self.source_directory = '/'.join(self.files[0].split('/')[:-1])
            self.files = [f.split('/')[-1] for f in self.files]

        if remove_prefixes:
            # remove prefix if the filename contains it
            self.files = [f[prefix_length:] if re.findall(prefix_regex, f) else f for f in self.files]

        # initially playlist name is set to source directory name
        self.playlist_name = self.source_directory.split('/')[-1]

        self.editor()

    def editor(self):
        self.editor_window = Toplevel()
        editor_window = self.editor_window
        editor_window.title(self.title)

        files = self.files
        playlist_name = self.playlist_name

        def draw_table():
            nonlocal frame
            frame.destroy()
            frame = Frame(canvas)
            canvas.create_window((0, 0), window=frame, anchor=NW)

            change_order_legend = Label(frame, text='Change Order')
            file_name_legend = Label(frame, text='File Name')
            remove_button_legend = Label(frame, text='Remove')

            change_order_legend.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
            file_name_legend.grid(row=0, column=3, padx=10, pady=10)
            remove_button_legend.grid(row=0, column=4, padx=10, pady=10)

            for index, file in enumerate(files):
                row_label = Label(frame, text=index + 1)
                up_button = Button(frame, command=partial(file_up, index), text='Up')
                if index == 0:
                    up_button.config(state=DISABLED)
                down_button = Button(frame, command=partial(file_down, index), text='Down')
                if index == len(files) - 1:
                    down_button.config(state=DISABLED)
                file_name_label = Entry(frame, width=100)
                file_name_label.insert(0, file)
                file_name_label.config(state=DISABLED, disabledforeground='black')
                remove_button = Button(frame, command=partial(file_remove, index), text='X')

                row = 1 + index
                row_label.grid(row=row, column=0, padx=10, pady=10)
                up_button.grid(row=row, column=1, padx=10, pady=10)
                down_button.grid(row=row, column=2, padx=10, pady=10)
                file_name_label.grid(row=row, column=3, padx=10, pady=10)
                remove_button.grid(row=row, column=4, padx=10, pady=10)

        def file_up(index):
            files[index], files[index - 1] = files[index - 1], files[index]
            draw_table()

        def file_down(index):
            files[index], files[index + 1] = files[index + 1], files[index]
            draw_table()

        def file_remove(index):
            del files[index]
            draw_table()

        def save_changes():
            self.playlist_name = playlist_name_field.get()
            if not self.playlist_name:
                self.playlist_name = 'Unnamed'
            self.save.set(True)

        playlist_name_field_label = Label(editor_window, text='Playlist (folder) name: ')
        playlist_name_field_label.grid(row=0, column=0, padx=10, pady=20)

        playlist_name_field = Entry(editor_window, width=50)
        playlist_name_field.grid(row=0, column=1, pady=20)
        playlist_name_field.insert(0, playlist_name)

        save_changes_button = Button(editor_window, command=save_changes, text='Save Changes')
        save_changes_button.grid(row=0, column=40, columnspan=10, padx=20, pady=20)

        main_frame = LabelFrame(editor_window)
        main_frame.grid(row=1, column=0, columnspan=50, padx=20, pady=20)

        canvas = Canvas(main_frame, width=1060, height=530)
        canvas.pack(side=LEFT, fill=BOTH, expand=1)

        scrollbar = ttk.Scrollbar(main_frame, orient=VERTICAL, command=canvas.yview)
        scrollbar.pack(side=RIGHT, fill=Y)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        frame = Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor=NW)
        draw_table()


def format_prefix(index):
    prefix = str(index + 1)
    prefix = f'[{(4 - len(prefix)) * "0"}{prefix}] '
    return prefix


def new_playlist_copy():
    title = 'New Playlist (create new folder with copies of files)'

    editor_instance = Editor(title)

    while True:
        root.wait_variable(editor_instance.save)
        if editor_instance.save:
            target_directory = filedialog.askdirectory(title='Select where to save your playlist')
            if target_directory:
                editor_instance.editor_window.destroy()
                break
            else:
                editor_instance.save = tkinter.BooleanVar()

    source_directory = editor_instance.source_directory
    files = editor_instance.files
    playlist_name = editor_instance.playlist_name

    target_path = os.path.join(target_directory, playlist_name)
    while True:
        try:
            os.mkdir(target_path)
            break
        except FileExistsError:
            target_path += ' (new version)'

    for index, file in enumerate(files):
        prefix = format_prefix(index)
        source_file_path = os.path.join(source_directory, file)
        new_filename = f'{prefix}{file}'
        target_file_path = os.path.join(target_path, new_filename)
        shutil.copyfile(source_file_path, target_file_path)

    os.startfile(target_path)


def new_playlist_existing():
    title = 'New Playlist (work on existing folder, not recommended)'

    editor_instance = Editor(title, working_on_existing_folder=True)
    root.wait_variable(editor_instance.save)
    editor_instance.editor_window.destroy()

    source_directory = editor_instance.source_directory
    old_files = [f for f in os.listdir(source_directory) if os.path.isfile(os.path.join(source_directory, f))]
    new_files = editor_instance.files
    playlist_name = editor_instance.playlist_name

    # rename directory
    if playlist_name != source_directory:
        new_directory = source_directory.split('/')
        del new_directory[-1]
        new_directory.append(playlist_name)
        new_directory = '/'.join(new_directory)
        while True:
            try:
                os.rename(source_directory, new_directory)
                break
            except FileExistsError:
                new_directory += ' (new version)'
        source_directory = new_directory

    for file in old_files:
        if file not in new_files:
            os.remove(os.path.join(source_directory, file))

    for index, file in enumerate(new_files):
        prefix = format_prefix(index)
        source_file_path = os.path.join(source_directory, file)
        new_filename = f'{prefix}{file}'
        target_file_path = os.path.join(source_directory, new_filename)
        os.rename(source_file_path, target_file_path)

    os.startfile(source_directory)


def edit_playlist():
    title = 'Edit Existing FilenamePlaylistMaker Playlist'

    editor_instance = Editor(title, working_on_existing_folder=True, remove_prefixes=True)
    root.wait_variable(editor_instance.save)
    editor_instance.editor_window.destroy()

    source_directory = editor_instance.source_directory
    old_files = [f for f in os.listdir(source_directory) if os.path.isfile(os.path.join(source_directory, f))]
    old_files_without_prefixes = [f[prefix_length:] if re.findall(prefix_regex, f) else f for f in old_files]
    new_files = editor_instance.files
    playlist_name = editor_instance.playlist_name

    # rename directory
    if playlist_name != source_directory:
        new_directory = source_directory.split('/')
        del new_directory[-1]
        new_directory.append(playlist_name)
        new_directory = '/'.join(new_directory)
        while True:
            try:
                os.rename(source_directory, new_directory)
                break
            except FileExistsError:
                new_directory += ' (new version)'
        source_directory = new_directory

    for file_with_prefix, file_without_prefix in zip(old_files, old_files_without_prefixes):
        if file_without_prefix not in new_files:
            os.remove(os.path.join(source_directory, file_with_prefix))

    for index, file in enumerate(new_files):
        prefix = format_prefix(index)
        old_filename = old_files[old_files_without_prefixes.index(file)]
        source_file_path = os.path.join(source_directory, old_filename)
        new_filename = f'{prefix}{file}'
        target_file_path = os.path.join(source_directory, new_filename)
        os.rename(source_file_path, target_file_path)

    os.startfile(source_directory)


new_playlist_copy_button = Button(root, text='New Playlist (create new folder with copies of files)',
                                  command=new_playlist_copy)
new_playlist_existing_button = Button(root, text='New Playlist (work on existing folder, not recommended)',
                                      command=new_playlist_existing)
edit_playlist_button = Button(root, text='Edit Existing FilenamePlaylistMaker Playlist', command=edit_playlist)

new_playlist_copy_button.grid(row=0, column=0, padx=20, pady=20)
new_playlist_existing_button.grid(row=0, column=1, padx=20, pady=20)
edit_playlist_button.grid(row=0, column=2, padx=20, pady=20)

root.mainloop()
