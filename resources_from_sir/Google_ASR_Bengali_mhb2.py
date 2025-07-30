
#import dircache
import os
global_cache = {}
def cached_listdir(path):
    res = global_cache.get(path)
    if res is None:
        res = os.listdir(path)
        global_cache[path] = res
    return res
#import num2words
import speech_recognition as sr
import pdb
import re
r = sr.Recognizer()


dir_name1=r"/mnt/md0/user_noor/imps/bopenslr_SE_asr_data_15k/Train/clean_15k/06527"

a = cached_listdir(dir_name1)
fo = open("bengali", "w")
for num in range(0,14):
  with sr.WavFile(dir_name1+'/'+a[num]) as source:     # use "test.wav" as the audio source
    audio = r.record(source)                     # extract audio data from the file
    try:
      #ASR_Result=r.recognize_google(audio, language='bn-BD')
      ASR_Result=r.recognize_google(audio, language='bn')
      print(str(num) +": "+ ASR_Result.encode("utf-8"))   # recognize speech using Google Speech Recognition
      #fo.write( )
      wavename=str(a[num]).split('.')[0]
      fo.write(ASR_Result.encode("utf-8")+' ('+wavename+')'+"\n")
    except:
      print("Google Speech Recognition could not understand audio")
      fo.write( '"*/'+a[num]+'.rec"'+"\n"+"."+"\n")
fo.close()