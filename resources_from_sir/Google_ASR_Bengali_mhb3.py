import os
import speech_recognition as sr
import pdb
#import re
r = sr.Recognizer()
def get_filepaths(directory):
    listOf_file_paths = list()
    for (root, directories, files) in os.walk(directory):
        listOf_file_paths += [os.path.join(root, file) for file in files if file.endswith('.wav')]
        #listOf_file_paths += [os.path.join(root, file) for file in files]
        #listOf_file_paths += [os.path.join(root, file) for file in files if file.upper().endswith('.TXT')]
    return listOf_file_paths

#dir_name=r"/mnt/md0/user_noor/imps/prac/bopenslr_se/train/cl_tr"
#dir_name="/mnt/md0/user_noor/imps/prac/bopenslr_se/train/cl_tr"
#dir_name="/mnt/md0/user_noor/imps/bopenslr_SE_asr_data_15k/Train/clean_15k"
dir_name="/mnt/md0/user_noor/imps/bopenslr_SE_asr_data_15k/Test/clean_ts/"
path_list= get_filepaths(dir_name)
fo = open("bopenslr_test_Google.transcription", "w")
for each in path_list:
  with sr.WavFile(each) as source:     # use "test.wav" as the audio source
    audio = r.record(source)                     # extract audio data from the file
    try:
      ASR_Result=r.recognize_google(audio, language='bn-BD')
      #ASR_Result=r.recognize_google(audio, language='bn')
      #print(each+": "+ ASR_Result.encode("utf-8"))   # recognize speech using Google Speech Recognition
      wavepath=each.split('/')[-1]
      wavename=wavepath.split('.')[0]
      pre=wavename.split('-')[0]
      last=wavename.split('-')[1]
      wavename=last+'-'+pre
      fo.write(ASR_Result.encode("utf-8")+' ('+wavename+')'+"\n")
      #fo.write(ASR_Result+' ('+wavename+')'+"\n")
    except:
      print("Google Speech Recognition could not understand audio")
      fo.write( '"'+each+'"'+"\n")
fo.close()