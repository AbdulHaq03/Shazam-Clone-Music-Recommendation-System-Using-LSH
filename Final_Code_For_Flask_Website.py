from flask import Flask, render_template, request, redirect, flash, session
import os
from werkzeug.utils import secure_filename
import pickle
import librosa
import numpy as np
from pymongo import MongoClient

client = MongoClient()
db = client['Music_Database']
collection = db['All_mp3']

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'C:/Users/ahaqu/OneDrive/Desktop/Data'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SECRET_KEY'] = 'mysecretkey'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'mp3'


@app.route('/')
def home():
    return render_template('Home.html')


@app.route('/music', methods=['GET', 'POST'])
def music():
    if request.method == 'POST':
        file = request.files.get('mp3file')
        if not file:
            return "No file uploaded"
        
        # INITIALIZE VARIABLES
        Final_band_1 = {}
        Final_band_2 = {}
        Audio_2 = []
        newlist = []
        anotherList = []
        Max = []
        Min: str = ''
        Per_1: str = ''
        Per_2: str = ''

        # LOAD PRE-TRAINED MODELS FOR QUERY
        with open(r"Final_bands_1.pkl", 'rb') as file1:
            Final_band_1 = pickle.load(file1)

        with open(r"Final_bands_2.pkl", 'rb') as file2:
            Final_band_2 = pickle.load(file2)

        with open(r"Permutations.pkl", 'rb') as file3:
            list_of_perm = pickle.load(file3)

        with open(r"MinHash_dict.pkl", 'rb') as file4:
            Minimum = pickle.load(file4)

        # LOAD THE UPLOADED FILE AND EXTRACT MFCC FEATURES BY USING LIBROSA LIBRARY
        
        y, sr = librosa.load(file, dtype='float32')
        MFCC = librosa.feature.mfcc(y=y, sr=sr)

        # CREATE A LIST OF RANDOM VECTORS AND PERFORM DOT PRODUCT WITH MFFCs
        for index, value in enumerate(MFCC):
            length_of_vector = len(MFCC[index])

            Random_vector = np.random.rand(length_of_vector, 1)

            Dot_product = np.dot(MFCC[index], Random_vector)

            Audio_2.append(Dot_product)

        # NORMALIZE Audio_2 LIST
        for index, value in enumerate(Audio_2):

            if value > 1:
                Audio_2[index] = 1
            elif value < 1:
                Audio_2[index] = 0

        # COMPUTE MINIMUM OF THE DOT PRODUCT VALUES FOR EACH RANDOM VECTOR
        for i in range(len(list_of_perm)):

            anotherList = []

            for j in range(len(Audio_2)):

                if Audio_2[j] == 1:
                    anotherList.append(list_of_perm[i][j])

            newlist.append(min(anotherList))

        # INITIALIZE TWO VARIABLES SUMS
        Sum1 = 0
        Sum2 = 0
        test_Audio = {}

        # TAKE SUM OF FIRST 5 AND LAST 5 NUMBERS FROM MINHASH
        for i in range(20):
            if i < 10:
                Sum1 += newlist[i]

            if i > 10:
                Sum2 += newlist[i]

        # ADD THOSE TO test_Audio DICTIONARY
        test_Audio['sum_1'] = Sum1
        test_Audio['sum_2'] = Sum2

        # SIMILARITY LISTS
        Similarity_1 = []
        Similarity_2 = []

        # CHECK THE SIMILARITY BETWEEN THE FILE UPLOADED
        for i in Final_band_1:
            if test_Audio['sum_1'] == i:
                Similarity_1 = Final_band_1[i]

        for i in Final_band_2:
            if test_Audio['sum_2'] == i:
                Similarity_2 = Final_band_2[i]

        # ADD BOTH SIMILARITIES AND GET UNIQUE FILES
        Similar = Similarity_1 + Similarity_2
        Similar = list(np.unique(Similar))

        # INITIALIZING VARIABLES
        Hash_sum = 0
        Jaccard = {}

        # GET JACCARD AND ITS PERCENTAGE OF HOW MUCH IT MATCHES
        for i in Similar:

            Hash_sum = 0

            for index, value in enumerate(newlist):

                if Minimum[i][index] == newlist[index]:
                    Hash_sum += 1

            Jaccard[i] = (Hash_sum / 20) * 100

        # GET THE FIRST OCCURRING VALUE WHICH IS 100% MATCHED
        already_added = []
        for index, value in enumerate(Jaccard):
            if Jaccard[value] == Jaccard[max(Jaccard, key=Jaccard.get)]:
                if value[5:] not in already_added:
                    Max.append(str(value[5:]))
                    already_added.append(value[5:])
                if len(Max) >= 5:
                    break

        i = 0

        # GET THE FIRST OCCURRING VALUE WHICH HAS THE LOWEST METRIC VALUE
        for index, value in enumerate(Jaccard):
            if Jaccard[value] == Jaccard[min(Jaccard, key=Jaccard.get)]:
                Min = str(value[5:])
                break

        # STORE INSIDE TWO STRINGS
        Per_1 = str(Jaccard[max(Jaccard, key=Jaccard.get)])
        Per_2 = str(Jaccard[min(Jaccard, key=Jaccard.get)])

        # THE MOST SIMILAR AND LEAST SIMILAR AUDIOS
        string_1 = 'MOST SIMILAR AUDIO IS ' + Max[0]
        string_2 = 'LEAST SIMILAR AUDIO IS ' + Min

        # THE SIMILARITY PERCENTAGES
        Per_1 = 'SIMILARITY : ' + Per_1
        Per_2 = 'SIMILARITY : ' + Per_2
        
        filename = Max[0]
        metadata = collection.find_one({'file_name': filename})

        title = metadata['title']
        artist = metadata['artist']
        album = metadata['album']
        genre = metadata['genre']

        filename_1 = Min
        metadata_1 = collection.find_one({'file_name': filename_1})

        title_1 = metadata_1['title']
        artist_1 = metadata_1['artist']
        album_1 = metadata_1['album']
        genre_1 = metadata_1['genre']

        try:
            filename_2 = Max[1]
            metadata_2 = collection.find_one({'file_name': filename_2})

            title_2 = metadata_2['title']
            artist_2 = metadata_2['artist']
            album_2 = metadata_2['album']
            genre_2 = metadata_2['genre']
        except IndexError:
            print("NO MAX[1]")

        try:
            filename_3 = Max[2]
            metadata_3 = collection.find_one({'file_name': filename_3})

            title_3 = metadata_3['title']
            artist_3 = metadata_3['artist']
            album_3 = metadata_3['album']
            genre_3 = metadata_3['genre']
        except IndexError:
            print("NO MAX[2]")

        try:
            return render_template('Music.html', string_1=string_1, title=title, artist=artist, album=album, filename=filename, genre=genre, string_2=string_2, title_1=title_1, artist_1=artist_1, album_1=album_1, genre_1=genre_1, filename_1=filename_1, filename_2=filename_2, filename_3=filename_3, title_2=title_2, title_3=title_3, artist_2=artist_2, artist_3=artist_3, album_2=album_2, album_3=album_3, genre_2=genre_2, genre_3=genre_3)
        except UnboundLocalError:
            print("WOW")

        try:
            return render_template('Music.html', string_1=string_1, title=title, artist=artist, album=album, filename=filename, genre=genre, string_2=string_2, title_1=title_1, artist_1=artist_1, album_1=album_1, genre_1=genre_1, filename_1=filename_1, filename_2=filename_2, title_2=title_2, artist_2=artist_2,album_2=album_2, genre_2=genre_2)
        except UnboundLocalError:
            print("WOW")
        
        try:
            return render_template('Music.html', string_1=string_1, title=title, artist=artist, album=album, genre=genre, filename=filename, string_2=string_2, title_1=title_1, artist_1=artist_1, album_1=album_1, genre_1=genre_1)
        except UnboundLocalError:
            print("WOW")

    return render_template('Music.html')


if __name__ == '__main__':
    app.run(debug=True)
