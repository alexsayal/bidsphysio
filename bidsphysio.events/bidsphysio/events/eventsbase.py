# TODO: make sure onset and duration are there and that they are float numbers in seconds

import json

import numpy as np
import pandas as pd


class EventSignal(object):
    """
    Individual events object (e.g., Eyelink events, task events)
    Members:
    --------
    label : str
        Event label (e.g., 'onset', 'duration', 'trial_type')
    units : str
    description : str
    event : list of numbers or strings
        The events information. Columns onset and duration are floats in seconds and are mandatory.
    type : str
        Describes the type of event ( str, int or float)
    """

    def __init__(
            self,
            label=None,
            units="",
            description="",
            event=[],
            type=""
            ):
        self.label = label
        self.units = units
        self.description = description
        self.event = event
        self.type = type
       

class EventData(object):
    """
    List of events objects. It has its own methods to write to file
    """

    def __init__(
            self,
            events = None,
            bidsprefix = None
            ):
        self.events = events if events is not None else []
        self.bidsprefix = bidsprefix

    def labels(self):
        """
        Returns a list with the labels of all the events columns
        """
        return [ item.label for item in self.events ]

    def append_event(self, event):
        """
        Appends a new events object to the events list
        """
        assert (
            isinstance(event, EventSignal)
        ), "You can only add EventSignals to EventData"

        if hasattr(self,'events'):
            self.events.append( event )
        else:
            self.events = [event]

    def set_bidsprefix(self, bidsprefix):
        """
        Sets the bidsprefix attribute for the class
        """

        # remove '_bold.nii(.gz)' or '_events' if present **at the end of the bidsPrefix**
        for mystr in ['.gz', '.nii', '_bold', '_events']:
            bidsprefix = bidsprefix[:-len(mystr)] if bidsprefix.endswith(mystr) else bidsprefix

        # Whatever is left, we assign to the bidsprefix class attribute:
        self.bidsprefix = bidsprefix

    def save_events_bids_json(self, json_fName):
        """
        Saves the events header information to the BIDS json file.
        It's the responsibility of the calling function to make sure they can all be saved in the same file.
        """

        # make sure the file name ends with "_events.json" by removing it (if present)
        #   and adding it back:
        for myStr in ['.json','_events']:
            json_fName = json_fName[:-len(myStr)] if json_fName.endswith( myStr ) else json_fName
        json_fName = json_fName + '_events.json'

        with open( json_fName, 'w') as f:
            json.dump({
                "Columns": [item.label for item in self.events],
                **{            # this syntax allows us to add the elements of this dictionary to the one we are creating
                    item.label: {
                        "Units": item.units
                    }
                    for item in self.events if item.units != ""
                      #item.label: {
                      # "Description": item.description
                      #}
                      #for item in self.events if item.description != ""
                }
            }, f, sort_keys = True, indent = 4, ensure_ascii = False)
            f.write('\n')

    def save_events_bids_data(self, data_fName):
        """
        Saves the EventData object to the BIDS .tsv.gz file.
        It's the responsibility of the calling function to make sure they can all be
        saved in the same file.
        """

        # make sure the file name ends with "_events.tsv.gz":
        for myStr in ['.gz','.tsv','_bold','_events']:
            if data_fName.endswith( myStr ):
                data_fName = data_fName[:-len(myStr)]
        
        data_fName = data_fName + '_events.tsv'

        # Save the data:
        myFmt=[]
        for item in self.events:
            if item.type == 'str':
                myfmt = '%s'
            elif item.type == 'int':
                myfmt = '%1d'
            elif item.type == 'float':
                myfmt = '%.4f'
            myFmt.append(myfmt)

        header=[item.label for item in self.events]
        header_str="\t".join(str(x) for x in header)
        with open(data_fName, 'wb') as f:
            f.write(header_str.encode('utf-8')+ b'\n')
            np.savetxt(
                       f,
                       np.transpose( [item.event for item in self.events] ),
                       fmt=myFmt,
                       delimiter='\t'
            )
        print('Saving task events')

    def append_events_bids_data(self, data_fName):
        """
        Appends the EventData object to the existing BIDS .tsv.gz file. Then opens the file an sorts the events based on their 'onset'.
        """
        
        # make sure the file name ends with "_events.tsv.gz":
        for myStr in ['.gz','.tsv','_bold','_events']:
            if data_fName.endswith( myStr ):
                data_fName = data_fName[:-len(myStr)]
    
        data_fName = data_fName + '_events.tsv'
        
        #If there is an 'eyetracker label' in self, append a new EventSignal to self
        if hasattr(self, 'Eyetracker'):
            self.append_event(
                EventSignal(
                            label = 'source',
                            event = np.array(['eyetracker']*len(self.events[0].event)),
                            type = 'str'
                )
        )
        
        # Save the data:
        myFmt=[]
        for item in self.events:
            if item.type == 'str':
                myfmt = '%s'
            elif item.type == 'int':
                myfmt = '%1d'
            elif item.type == 'float':
                myfmt = '%.4f'
            myFmt.append(myfmt)

        header=[item.label for item in self.events]
        header_str="\t".join(str(x) for x in header)
        with open(data_fName, 'ab') as f:
            f.write(header_str.encode('utf-8')+ b'\n')
            np.savetxt(
                       f,
                       np.transpose( [item.event for item in self.events] ),
                       fmt=myFmt,
                       delimiter='\t'
            )
        
        #Open file with appended data
        df = pd.read_csv(data_fName, sep='\t')
        ind = df.index[df['onset'] == 'onset'].tolist() #check if there's a second onset in the file
        if ind:
            #split in two dataframes
            df1 = df.iloc[:ind[0],:]
            df2 = df.iloc[ind[0]:,:]
            df2.columns = df2.iloc[0] # make new header
            df2 = df2[1:]   #drop header
            df1 = df1.append(df2) #merge two dataframes
            df1 = df1.dropna(axis=1, how='all') #drop columns that only have NaNs
            df1 = df1.replace(np.NaN, 'n/a') #drop columns that contain only NaNs
            df1.onset = df1.onset.astype(float)
            df1.duration = df1.duration.astype(float)
            df1 = df1.sort_values(by=['onset'], ascending=True) #sort based on onset
            df1 = df1.drop_duplicates(ignore_index=False) #drop duplicates
            df1.to_csv(data_fName,sep='\t', index=False)  #save to file
        
        print('Saving task events')
        
    def save_events_to_bids(self, bids_fName=None):
        """
        Saves the EventData sidecar '.json' file(s) and signal(s).
        It saves all events in a single .json/.tsv.gz pair.
        """
        
        if bids_fName:
            # if bids_fName argument is passed, use it:
            self.set_bidsprefix(bids_fName)
        else:
            # otherwise, check to see if there is already a 'bidsprefix'
            # for this instance of the class. If neither of them is
            # present, return an error:
            if not self.bidsprefix:
                raise Exception('fileName was not a known provided')
        
        print('Saving events files')
        self.save_events_bids_json(self.bidsprefix)
        self.save_events_bids_data(self.bidsprefix)

    print('')
