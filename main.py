import sys
import tkinter as tk
import time
from multiprocessing.dummy import Process
from datetime import datetime
from tkinter import messagebox as mb
from tkinter import Scrollbar
from tkinter import simpledialog as sd
from tkinter import filedialog as fd

VERSION_NUMBER = "0.1"

try:
    sys.path.append('./ipatoolpy/') # Prevent ipatool-py submodules from crashing
    from ipatoolpy.main import *
    IMPORTED_IPATOOL = True
except:
    IMPORTED_IPATOOL = False
    
class ipatool_arg:
    pass

def get_name(val):
    return val["name"]

class EasyIPAGUI:
    def __init__(self, args = []):
        # Import ipatool-py, ensure that it is properly working before continuing
        if IMPORTED_IPATOOL:
            self.ipatool = IPATool()
        else:
            result = mb.askyesno("Cannot initialise ipatool-py!",
                #TODO: Auto install requirements
                #message="Cannot initialise ipatool-py! Please ensure the requirements are installed before using this tool. Would you like to install them now?")
                message="Cannot initialise ipatool-py! Please ensure the requirements are installed before using this tool. (run pip3 install requirements.txt)")
            if result:
                pass
            else:
                return
    
        self.applist = []
        self.versionlist = []
        self.path = "."
        
        # Init configurable options    
        self.settings_write_metadata = True
        self.settings_skip_confirmation = False
        
        # Public so it can be killable
        self.app_process = None
        
        # Init a lot of the GUI
        # Main window with app list
        self.tk = tk.Tk()
        self.tk.rowconfigure(0,weight=1,minsize=100)
        self.tk.columnconfigure(0,weight=1,minsize=200)
        self.tk.minsize(width=800,height=620)
        self.tk.title("Easy ipa GUI - %s"%VERSION_NUMBER)
        self.tk.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(master=self.tk)
        self.canvas.grid(row=0, column=0, sticky="news")
        h = Scrollbar(master=self.tk, orient = 'vertical',command=self.canvas.yview)
        h.grid(row=0, column=1, sticky='ns')
        self.canvas.configure(yscrollcommand=h.set)
        self.inner_view = tk.Frame(master=self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_view, anchor='nw')
        inner_view_label = tk.Label(self.inner_view,text="No apps to display")
        inner_view_label.pack()
        self.inner_view.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
        # Bottom bar of the main window
        bottom = tk.Frame(master=self.tk, height=30);
        bottom.grid(row=1, column=0,sticky="ew")
        bottom.rowconfigure(0,weight=1)
        signin_button = tk.Button(bottom,text="Sign in",command=self.button_showloginprompt)
        signin_button.grid(row=0,column=0,sticky="w",padx=10)
        options_button = tk.Button(bottom,text="Options")
        options_button.grid(row=0,column=1,sticky="w",padx=10)
        manual_button = tk.Button(bottom,text="Enter App ID Manually")
        manual_button.grid(row=0,column=2,sticky="w",padx=10)
        toggle_frame = tk.Frame(bottom)
        toggle_frame.grid(row=0,column=3,sticky="w",padx=10)
        toggle_label = tk.Label(toggle_frame,text="Toggle All:")
        toggle_label.grid(row=0,column=0,sticky="w",padx=10)
        none_button = tk.Button(toggle_frame,text="Skip",command=self.button_togglenone)
        none_button.grid(row=0,column=1,sticky="w",padx=2)
        one_button = tk.Button(toggle_frame,text="Latest",command=self.button_toggleone)
        one_button.grid(row=0,column=2,sticky="w",padx=2)
        all_button = tk.Button(toggle_frame,text="All",command=self.button_toggleall)
        all_button.grid(row=0,column=3,sticky="w",padx=2)
        go_button = tk.Button(bottom,text="Begin",command=self.button_begin)
        go_button.grid(row=0,column=4,sticky="w",padx=10)
        
        # Options window
        self.options = tk.Toplevel(self.tk)
        self.options.withdraw()
        self.options.title("Options")
        self.options.protocol("WM_DELETE_WINDOW", self.options.withdraw)
        
        # Sign in window
        self.signin = tk.Toplevel(self.tk)
        self.signin.withdraw()
        self.signin.title("Sign In")
        self.signin.resizable(False, False)
        self.signin.protocol("WM_DELETE_WINDOW", self.signin.withdraw)
    
        username_label = tk.Label(self.signin,text="Apple ID")
        username_label.grid(row=0,column=0,sticky="w",padx=10)
        self.username = tk.Entry(self.signin,width=50)
        #self.username = tk.Entry(self.signin,width=50,show="*") #For demonstration/videos where you need to censor your username
        self.username.grid(row=0,column=1,sticky="w",padx=10)
        password_label = tk.Label(self.signin,text="Password")
        password_label.grid(row=1,column=0,sticky="w",padx=10)
        self.password = tk.Entry(self.signin,width=50,show="*")
        self.password.grid(row=1,column=1,sticky="w",padx=10)
        signin_button = tk.Button(self.signin,text="Sign in",command=self.button_login)
        signin_button.grid(row=2,column=1,sticky="w",padx=10)
        
        # Download window
        self.download = tk.Toplevel(self.tk)
        self.download.withdraw()
        self.download.title("Downloading")
        self.download.resizable(False, False)
        self.download.protocol("WM_DELETE_WINDOW", self.button_cancel_download)
        #TODO: Perhaps a better way of managing the state/preventing continuing too early? For now it works though
        self.download_state = False
        self.prepared_state = False
        self.downloading_apps_state = False
        self.download_label = tk.Label(self.download,text="Preparing to download...",width=60,justify="left",anchor="w")
        self.download_label.grid(row=0,column=0,sticky="w",padx=10)
        self.download_estimte_label = tk.Label(self.download,text="App Size Estimate: ",width=60,justify="left",anchor="w")
        self.download_estimte_label.grid(row=1,column=0,sticky="w",padx=10)
        
        # GUI is ready, hand off to main loop
        self.tk.mainloop()
        
    def button_cancel_download(self):
        result = mb.askyesno("Cancel",
            message="Would you like to cancel downloading?")
        if result:
            logger.info("Cancel has been requested, and will happen after current download.")
            self.download_estimte_label["text"]="Cancelling..." 
            self.download_cancel_state = True
        
    def button_showloginprompt(self):
        self.signin.deiconify()
        
    def button_login(self):
        self.signin.withdraw()
        # If it is currently grabbing the icons, we should kill that process. We will just restart the pool
        #TODO: Find better way of doing this??
        if self.app_process:
            if self.app_process.is_alive():
                self.app_process.terminate()
          
        signin_success = self.signin_client(self.username.get(), self.password.get())
        if signin_success:
            self.signin_success()
        else:
            # We don't know if an unsuccessful sign in is just because of 2FA, so we ask the user.
            #TODO: Find a way to tell if 2FA code was sent
            result = mb.askyesno(title="Enter 2FA Code",
                message="There was an issue with signing in. Did you receive a two-facter authentication code?"
            )
            if result:
                text = str(sd.askinteger("Enter 2FA Code", "Enter 2FA Code:"))
                signin_success = self.signin_client(self.username.get(), self.password.get()+text)
                if signin_success:
                    self.signin_success()
                else:
                    mb.showerror(title="Unable to sign in",
                    message="There was an issue signing in.")
                    self.signin.deiconify()
            else:
                self.signin.deiconify()
    
    def button_togglenone(self):
        for item in self.applist:
            if item["selection"]:
                item["selection"].selection_clear(0,2)
                item["selection"].selection_set(0)
        
    def button_toggleone(self):
        for item in self.applist:
            if item["selection"]:
                item["selection"].selection_clear(0,2)
                item["selection"].selection_set(1)
            
    def button_toggleall(self):
        for item in self.applist:
            if item["selection"]:
                item["selection"].selection_clear(0,2)
                item["selection"].selection_set(2)
                
    def button_begin(self):
        #Make sure we are ready to begin!
        if self.download_state and not self.downloading_apps_state:
            self.path = fd.askdirectory()
            if self.path:
                logger.info("Path has been selected as %s" % self.path)
                self.signin.withdraw()
                self.options.withdraw()
                self.tk.withdraw()
                self.download.deiconify()
                p = Process(target=self.get_app_version_list, args=[])       
                p.start()
                
    def signin_success(self):
        self.destroy_view()
        loading_label = tk.Label(self.inner_view,text="Loading Apps...")
        loading_label.pack()    
        self.app_process = Process(target=self.get_applid_history_list, args=[])       
        self.app_process.start()
        
    def get_app_version_list(self):
        self.prepared_state = False
        self.download_label["text"]="Apps to download: (0 apps found)"
        self.download_estimte_label["text"]="App Size Estimate: %.3sGB - %.3sGB" % (0,0)
        self.versionlist = []
        filesize_estimate = 0
        filesize_estimate_low = 0
        app_count = 0
        logger.info("Preparing download queue.")
        list_count = 0
        self.download_cancel_state = False
        for item in self.applist: 
            list_count+=1
            if item["selection"].curselection():
                option=item["selection"].curselection()[0]
                if option!=0:
                    logger.info("Trying appid %s"%item["id"])
                    evids, size, fullsize = self.get_app_evids(item["id"],return_all=option==2)
                    i=0
                    for evid in evids:
                        app_vrs = {}
                        app_vrs["id"] = item["id"]
                        app_vrs["evid"] = evid
                        self.versionlist.append(app_vrs)
                        app_count+=1
                        #My very scientifically proven method backed by multiple sources to estimate file size
                        filesize_estimate+=size
                        filesize_estimate_low+=size*(100/(100+i))
                        self.download_label["text"]="Preparing to download... %s of %s (%s versions)"%(list_count,len(self.applist),app_count)
                        self.download_estimte_label["text"]="App Size Estimate: %.3fGB - %.3fGB" % (filesize_estimate_low/1000000000,filesize_estimate/1000000000)
                        i+=1
                    
            if self.download_cancel_state:
                self.download.withdraw()
                self.tk.deiconify()
                self.downloading_apps_state = False
                return
                              
        time.sleep(1) #Get the message box updates
        self.prepared_state = True
        self.download_label["text"]="Apps to download: %s of %s (%s versions)"%(list_count,len(self.applist),app_count)
        self.download_estimte_label["text"]="App Size Estimate: %.3f GB - %.3f GB" % (filesize_estimate_low/1000000000,filesize_estimate/1000000000)
        if not self.settings_skip_confirmation:
            result = mb.askyesno("Begin?",
                message="Ready to download. Would you like to begin?")
            if not result:
                self.download.withdraw()
                self.tk.deiconify()
                return
                
        self.get_apps()
        
    
    def get_apps(self):
        self.downloading_apps_state = True
        self.download_cancel_state = False
        list_count = 1
        self.download_estimte_label["text"]=""
        for app in self.versionlist:
            self.download_label["text"]="Downloading... (%s of %s)"%(list_count,len(self.versionlist))
            should_try_again = True
            while should_try_again:
                try:
                    self.download_app(app["id"], app["evid"])
                    self.download_estimte_label["text"]="Finished downloading %s with evid %s" % (app["id"],app["evid"])
                    should_try_again = False
                except Exception as e:
                    self.download_estimte_label["text"]="Failed downloading %s with evid %s" % (app["id"],app["evid"])
                    time.sleep(0.3)
                    result = mb.askyesnocancel("Failed to download",
                        message="Failed to download app %s for version %s. Perhaps your storage has filled up. Would you like to select a new file location?"%(app["id"], app["evid"]))
                    if result==None:
                        result = mb.askyesno("Are you sure?",
                            message="Are you really sure you would like to cancel?")
                        if result:
                            self.downloading_apps_state = False
                            self.download.withdraw()
                            self.tk.deiconify()
                            return
                    elif result:
                        oldpath = self.path
                        self.path = fd.askdirectory()
                        if not self.path:
                            self.path = oldpath
                        else:
                            self.download_estimte_label["text"]="Updated file path to %s" % self.path
                    #TODO: Option to skip or stop in settings       
            list_count+=1
            if self.download_cancel_state:
                    self.download.withdraw()
                    self.tk.deiconify()
                    self.downloading_apps_state = False
                    return
        
        mb.showinfo("Finished",
                message="Downloads have finished!")
        self.downloading_apps_state = False
        self.download.withdraw()
        self.tk.deiconify()
    
    def get_client(self):
        if not self.ipatool_args:
            return None
        
        try:
           return self.ipatool._get_StoreClient(self.ipatool_args)
           #Currently there is a bug where this doesn't work after 30 seconds
           #So if that happens we sign in again
        except:
            self.ipatool.storeClientCache = {}
            return self.ipatool._get_StoreClient(self.ipatool_args)
    
    def signin_client(self, appleid, password):
        #Completely get rid of store client and try signing in again
        self.store_client = None
        args = ipatool_arg()
        args.appleid = appleid
        args.password = password
        args.itunes_server = False
        args.session_dir = None
        self.ipatool_args = args
        self.ipatool.storeClientCache = {}
        try:
            self.store_client = self.ipatool._get_StoreClient(args)
            return True #Should get here if sign in was successful
        except:
            return False
            
    def destroy_view(self):
        for widgets in self.inner_view.winfo_children():
            widgets.destroy()
            
    def destroy_app_checkboxes(self):
        for item in self.applist:
            if item["selection"]:
                item["selection"].destroy()
                item["selection"] = None
            
    def populate_app_view(self):
        self.download_state = False
        logger.info("Populating app view with %s apps."% len(self.applist))
        frame = tk.Frame(master=self.inner_view, bg="blue")
        frame.pack()
        self.inner_view.rowconfigure(0,weight=1)
        row = 0
        self.destroy_view()
        for item in self.applist:
            #Create label 
            name_label = tk.Label(self.inner_view,text=item["name"],justify="left",wraplength=360,width=40,anchor="w")
            name_label.grid(row=row,column=0,sticky="w",padx=10)
            id_label = tk.Label(self.inner_view,text=item["id"],justify="left")
            id_label.grid(row=row,column=1,sticky="w",padx=10)
            #Create Toggle Boxes
            boxes = {}
            boxes["id"] = item["id"]
            listbox = tk.Listbox(self.inner_view, selectmode = "single",height=3,width=5,selectbackground="gray",exportselection=0) 
            listbox.insert(tk.END, "Skip") 
            listbox.insert(tk.END, "Latest") 
            listbox.insert(tk.END, "All") 
            listbox.grid(row=row,column=2,sticky="w")
            listbox.selection_set(1)
            item["selection"]=listbox
            row+=1
        time.sleep(0.5) #Hacky way of getting the scrollbar to be correct
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.download_state = True
            
    def get_applid_history_list(self):
        self.download_state = False
        self.applist = []
        """
        TODO: Better way of getting years
        Unfortunately though, the iTunes API doesn't want to work for some reason. Apple
        for some reason doesn't like the mz_at_ssl-Dsid cookie that ipatool-py provides. For
        now, we just brute force the API to get all valid years.
        """
        yearlist = range(2008,datetime.now().year+1)
        for year in yearlist:
            logger.info("Doing year %s"%year)
            current_page = 1
            should_continue = True
            while should_continue:
                Store = self.get_client()
                try:
                    resp = Store.purchases(str(year), page=current_page)
                    logger.info("Got response! %s for page %s" % (len(resp.data.attributes.purchases),current_page))
                    current_page+=1
                    if len(resp.data.attributes.purchases) == 0:
                        should_continue = False
                    for i in resp.data.attributes.purchases:
                        if (i.items[0].kind=="iOS App"):
                            name=i.items[0].item_name
                            ida=i.items[0].item_id
                            app_dict = {}
                            app_dict["name"] = name
                            app_dict["id"] = ida
                            self.applist.append(app_dict)
                        
                except StoreException as e:
                    mb.showerror(title="Unable to get app list",
                        message="There was an issue getting the app list.")   
        print("done")
        self.applist.sort(key=get_name)
        self.populate_app_view()
        
    def get_app_evids(self, appId, return_all=True):
        Store = self.get_client()
        downResp = Store.download(appId, None, isRedownload=True) #Should always be redownload
        if not downResp.songList:
            logger.fatal("Failed to get app download info!")
            raise StoreException('download', downResp, 'no songList')
        downInfo = downResp.songList[0]
        appSize = downInfo.asset_info.file_size
        fullSize = downInfo.uncompressedSize
        if return_all:
            return downInfo.metadata.softwareVersionExternalIdentifiers,appSize,fullSize
        else:
            return [downInfo.metadata.softwareVersionExternalIdentifier],appSize,fullSize
        
    def download_app(self, appId, appVerId):
        #This is based on, but slightly modified from the ipatool-py downloading method (self.ipatoolpy.downloadOne)

        logger.info("Downloading appId %s appVerId %s", appId, appVerId)
        Store = self.get_client()
        logger.info('Retrieving download info for appId %s%s' % (appId, " with versionId %s" % appVerId if appVerId else ""))

        downResp = Store.download(appId, appVerId, isRedownload=True)
        logger.debug('Got download info: %s', downResp.as_dict())
        
        if not downResp.songList:
            logger.fatal("failed to get app download info!")
            raise StoreException('download', downResp, 'no songList')
        downInfo = downResp.songList[0]

        appName = downInfo.metadata.bundleDisplayName
        appId = downInfo.songId
        appBundleId = downInfo.metadata.softwareVersionBundleId
        appVerId = downInfo.metadata.softwareVersionExternalIdentifier
        # when downloading history versions, bundleShortVersionString will always give a wrong version number (the newest one)
        # should use bundleVersion in these cases
        appVer = downInfo.metadata.bundleVersion

        logger.info(f'Downloading app {appName} ({appBundleId}) with appId {appId} (version {appVer}, versionId {appVerId})')

        # if self.appInfo:
        filename = '%s-%s-%s-%s.ipa' % (appBundleId,
                                        appVer,
                                        appId,
                                        appVerId)
        # else:
        #     filename = '%s-%s.ipa' % (self.appId, appVerId)

        filepath = os.path.join(self.path, filename)
        logger.info("Downloading ipa to %s" % filepath)
        downloadFile(downInfo.URL, filepath)
        metadata = downInfo.metadata.as_dict()
        logger.info("Writing out iTunesMetadata.plist...")
        if zipfile.is_zipfile(filepath) and self.settings_write_metadata:
            with zipfile.ZipFile(filepath, 'a') as ipaFile:
                logger.debug("Writing iTunesMetadata.plist")
                ipaFile.writestr(zipfile.ZipInfo("iTunesMetadata.plist", get_zipinfo_datetime()), plistlib.dumps(metadata))
                logger.debug("Writing IPAToolInfo.plist")
                ipaFile.writestr(zipfile.ZipInfo("IPAToolInfo.plist", get_zipinfo_datetime()), plistlib.dumps(downResp.as_dict()))

                def findAppContentPath(c):
                    if not c.startswith('Payload/'):
                        return False
                    pathparts = c.strip('/').split('/')
                    if len(pathparts) != 2:
                        return False
                    if not pathparts[1].endswith(".app"):
                        return False
                    return True
                appContentDirChoices = [c for c in ipaFile.namelist() if findAppContentPath(c)]
                if len(appContentDirChoices) != 1:
                    raise Exception("failed to find appContentDir, choices %s", appContentDirChoices)
                appContentDir = appContentDirChoices[0].rstrip('/')

                processedSinf = False
                if (appContentDir + '/SC_Info/Manifest.plist') in ipaFile.namelist():
                    #Try to get the Manifest.plist file, since it doesn't always exist.
                    scManifestData = ipaFile.read(appContentDir + '/SC_Info/Manifest.plist')
                    logger.debug("Got SC_Info/Manifest.plist: %s", scManifestData)
                    scManifest = plistlib.loads(scManifestData)
                    sinfs = {c.id: c.sinf for c in downInfo.sinfs}
                    if 'SinfPaths' in scManifest:
                        for i, sinfPath in enumerate(scManifest['SinfPaths']):
                            logger.debug("Writing sinf to %s", sinfPath)
                            ipaFile.writestr(appContentDir + '/' + sinfPath, sinfs[i])
                        processedSinf = True
                if not processedSinf:
                    logger.info('Manifest.plist does not exist! Assuming it is an old app without one...')
                    infoListData = ipaFile.read(appContentDir + '/Info.plist') #Is this not loaded anywhere yet?
                    infoList = plistlib.loads(infoListData)
                    sinfPath = appContentDir + '/SC_Info/'+infoList['CFBundleExecutable']+".sinf"
                    logger.debug("Writing sinf to %s", sinfPath)
                    #Assuming there is only one .sinf file, hence the 0
                    ipaFile.writestr(sinfPath, downInfo.sinfs[0].sinf)
                    processedSinf = True

            logger.info("Downloaded ipa to %s" % filename)
        else:
            plist = filepath[:-4]+".info.plist"
            with open(plist, "wb") as f:
                f.write(plistlib.dumps(downResp.as_dict()))
            plist = filepath[:-4]+".plist"
            with open(plist, "wb") as f:
                f.write(plistlib.dumps(metadata))
            logger.info("Downloaded ipa to %s and plist to %s" % (filename, plist))
        """
        # Unsure if we care about this functionality yet so for now it is commented out
        self._outputJson({
            "appName": appName,
            "appBundleId": appBundleId,
            "appVer": appVer,
            "appId": appId,
            "appVerId": appVerId,

            "downloadedIPA": filepath,
            "downloadedVerId": appVerId,
            "downloadURL": downInfo.URL,
        })
        """
    
if __name__ == '__main__':
    if len(sys.argv) > 1:
        args = sys.argv[1:]
    else:
        args = []
    p = EasyIPAGUI(args)