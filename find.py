# -*- coding: utf-8 -*-
#!/usr/bin/env python

from __future__ import division
import Queue
import threading
import time
import urllib
import os
import re
import sys

stateLock = threading.Lock()


class website:
    """
    Sedang menangani pemformatan URL
    Done... Memeriksa Apakah Website Ini Aktif...
    """

    def __init__(self, data):
        site = data
        if not data.startswith("http"):
            site = "http://" + site
        if not site.endswith("/"):
            site = site + "/"
        self.address = site

        print("[?] Memeriksa apakah situs web aktif")
        statusCode = self.checkStatus(self.address)
        if statusCode == 200:
            print("[+] Situs web terlihat aktif!")
        elif statusCode == 404:
            print("[-] Situs web terlihat down")
            exit()
        else:
            print("[?] Gagal... website dirancang anti finder : ", statusCode)
            exit()

        self.checkRobot(self.address)

    def checkStatus(self, address):
        """ Fungsi ini mengembalikan status situs web """
        try:
            return urllib.urlopen(address).getcode()
        except IOError:
            print("[!] Gagal... Pastikan url anda tidak valid.")
            exit()


    def checkRobot(self,address):
        """
        Sedang memeriksa apakah robots.txt/robot.txt ada
        Baik... Jalur admin sudah ada di sana!
        """
        print("[?] Sedang Memeriksa file robot...")
        path = ["robot.txt","robots.txt"]
        urls = [address + i for i in path]

        for url in urls:
            statusCode = self.checkStatus(url)
            if statusCode == 200:
                print("\n[+] %s \n[+] Terlihat Ada, membaca konten..." % url)
                info = self.parseDir(url)
                if info:
                    print("[=] Informasi menarik ditemukan di file robot!")
                    print("="*80)
                    for line in info:
                        print "\t"+line
                    print("="*80)

                    try:
                        raw_input("[+] Tekan Ctrl + C untuk berhentikan program")
                    except KeyboardInterrupt:
                        os._exit(1)
                else:
                    print("[-] Tidak ada yang berguna ditemukan di file robot! melanjutkan program...")

    def getPage(self, address):
        return urllib.urlopen(address).readlines()

    def parseDir(self, address):
        DirPattern = re.compile(r".+: (.+)\n")
        interestingInfo = []
        dirs = []
        keyword = ["admin","Administrator","login","user","controlpanel",
                   "wp-admin","cpanel","userpanel","client","account"]

        page = self.getPage(address)
        # Parsing the robot file content for directory
        for line in page:
            if DirPattern.findall(line):
                dirs.append(DirPattern.findall(line)[0])

        # Checking if the directory contains juicy information
        for key in keyword:
            for directory in dirs:
                if key in directory:
                    interestingInfo.append(directory)
        return interestingInfo

class wordlist:
    """ Sedang memuat wordlist... """
    def __init__(self):
        try:
            # read the file and remove \n at the line ending
            self.load = [i.replace('\n', '') for i in open('wordlist.txt').readlines()]
        except IOError:
            print("[!] I/O Kesalahan, wordlist.txt Tidak ditemukan")


class scanThread(threading.Thread):
    """ Kelas ini adalah cetak biru yang digunakan untuk menghasilkan thread """
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.queue = q

    def run(self):
        while not self.queue.empty():
        # While queue is not empty, which means there is work to do
            stateLock.acquire()
            url = self.queue.get()
            stateLock.release()
            if self.online(url):
                stateLock.acquire()
                print("\n\n[+] Selesai! Halaman Admin Ditermukan dalam waktu %.2f detik" % (time.time() - starttime))
                print("[=] %s" % url)
                raw_input("[+] Tekan enter untuk keluar!")
                print("[+] Siap Laksanakan! Keluar dari Program...")
                os._exit(1)

            else:
                stateLock.acquire()
                #print("[-] Tried : %s" % url)
                stateLock.release()
            self.queue.task_done()
            # Release task completed status

    def online(self, url):
        """ Mengembalikan True jika urlnya online AKA kode status HTTP == 200 """
        try:
            return urllib.urlopen(url).getcode() == 200
        except IOError:
            stateLock.acquire()
            print("[!] Kesalahan Resolusi Nama")
            stateLock.release()


def main():
    try:
        pathlist = wordlist().load
        # loads the wordlist
        address = website(raw_input("[+] Berikan website yang ingin di scan : ")).address
        mainApp(address, pathlist)
        # Runs the main Application
    except KeyboardInterrupt:
        print("\n[-] Ctrl + C Terdeteksi!")
        print("[-] Keluar...")
        os._exit(1)


def progressBar(q):
    symbol = "="
    emptySymbol = "-"
    maxJob = q.qsize()
    maxlinesize = 20
    while not q.empty():
        current = q.qsize()
        currentProgress = 100 - ((current / maxJob) * 100)
        #print "Current : %s, progress = %s, maxJob = %s" % (current,currentProgress,maxJob)
        if currentProgress < 95:
            bar = symbol * int(currentProgress/(100/maxlinesize))
        elif currentProgress > 95:
            bar = symbol * maxlinesize
        remaining = emptySymbol * (maxlinesize - len(bar))
        line = "\rTunggu! Sedang mencari... : [%s%s] %.2f%%" % (bar,remaining,currentProgress)
        #line = "\rو︻̷┻̿═━一 [%s%s] %.2f%%" % (bar, remaining,currentProgress)
        threading.Thread(target=printoutput,args=(line,)).start()
        # sys.stdout.write(line)
        # sys.stdout.flush()
        # time.sleep(1)

def printoutput(data):
    stateLock.acquire()
    sys.stdout.write(data)
    sys.stdout.flush()
    stateLock.release()
    time.sleep(0.5)



class mainApp:
    def __init__(self,address,plist):
        self.address = address
        self.wordlist = plist
        self.createJobs()
        self.run()

    def createJobs(self):
        """
        Bergabung dengan alamat situs web dengan jalur admin dari wordlist
        dan tambahkan ke antrian
        """
        self.queue = Queue.Queue()
        stateLock.acquire()
        for path in self.wordlist:
            self.queue.put(self.address + path)
        stateLock.release()

    def run(self):
        try:
            print("[!] - XSkull7 Tools")
            threadCount = raw_input("[+] Masukkan jumlah thread max 20! : ")
            if not threadCount:
                print("[=] Jumlah thread = 20")
                threadCount = 20
            else:
                print("[=] Jumlah thread = %d" % int(threadCount))

            threadList = []
            global starttime
            starttime = time.time()

            progressbar = threading.Thread(target=progressBar,args=(self.queue,))
            progressbar.daemon = True
            progressbar.start()

            for i in range(0, int(threadCount)):
                thread = scanThread(self.queue)
                #thread.daemon = True
                threadList.append(thread)
                thread.start()
            # Waiting for all threads to finish
            self.queue.join()
            print("\n\n[=] Waktu berlalu selama : %.2f detik" % float(time.time()-starttime))
            print("[-] Maaf... halaman admim tidak ketemu!")
            progressbar.join()
            for thread in threadList:
                thread.join()
        except KeyboardInterrupt:
            stateLock.acquire()
            print("\n[~] Ctrl + C Terdeteksi!")
            print("[~] Keluar...")
            os._exit(1)

if __name__ == "__main__":
    main()
