import datetime
import json
import pathlib
from typing import Dict, List

import IPython


class ImplantSVG:
    "Functions for displaying and interacting with DR implant image"
    
    DR1_SVG = pathlib.Path(R"\\allen\programs\mindscope\workgroups\dynamicrouting\ben\implants\DR1.svg")
    "Default - labelled .svg of first production DR implant, known as DR1, TS-5, 2002"
    path:pathlib.Path = DR1_SVG
    svg:str = path.open('r').read()    
    labels = {
        'A':[1,2,3],
        'B':[1,2,3,4],
        'C':[1,2,3,4],
        'D':[1,2,3],
        'E':[1,2,3,4],
        'F':[1,2,3],
    } 
    "Available integer labels for each probe"
    strings:List[str] = list(f"{k}{i}" for k,v in labels.items() for i in v)
    "Original labels for each hole: A1, A2, A3, B1, B2, B3, B4, etc."
    hole_memory_default:dict = dict(zip(strings,strings))
    "Lookup table so we can find the current textlabel for a given hole - original set in case we need to reset"
    
    def __init__(self, path:None|str|pathlib.Path=None):
        "Instantiate if we need to keep track of probe/hole assignments"
        if path:
            self.path = pathlib.Path(path)
            self.svg:str = self.path.open('r').read()    
        if self.targets_path.exists():
            self.load_targets()
        else:
            self.probe_memory:Dict[str,str|None] = dict(zip(list('ABCDEF'),[None]*6))
            "Assigned hole for each probe - effectively `hole_memory` reversed"
        self.hole_memory:Dict[str,str|None] = dict(zip(self.strings,[None]*len(self.strings)))
        "Lookup table so we can find the current textlabel for a given hole"
        # added so we can store an image and keep modifying it, instead of re-loading
        # from disk every re-draw, but reloading seems fast enough - this could just be
        # worked out from probe_memory to avoid having to manually sync the two 
    
    date_today: str = datetime.datetime.today().strftime("%Y%m%d") 
    records_dir = (DR1_SVG.parent / 'insertion_records')
    records_path = records_dir / (date_today + '_insertion_record.json')
    targets_dir = (DR1_SVG.parent / 'insertion_targets')
    targets_path = targets_dir / (date_today + '_insertion_targets.json')
    
    @classmethod
    def targets_to_disk(cls, targets:Dict[str,str|None], path:str|pathlib.Path=targets_path):
        "Save current probe_memory to file"
        path = pathlib.Path(path)
        path = path.with_suffix('.json')
        path.parent.mkdir(exist_ok=True, parents=True)
        path.touch()
        with open(path, 'w') as f:
            json.dump(targets, f, indent=4, sort_keys=True)
        
    @classmethod
    def targets_from_disk(cls, path:str|pathlib.Path=targets_path) -> None|dict:
        "Load probe_memory from file"
        path = pathlib.Path(path)
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
        return None
            
    def save(self, path:str|pathlib.Path=records_path):
        self.targets_to_disk(self.probe_memory, path)
    
    def load_targets(self, path:str|pathlib.Path=targets_path):
        if targets := self.targets_from_disk(path):
            self.probe_memory = targets
            for label in self.strings:
                for k,v in self.probe_memory.items():
                    if v == label:
                        self.hole_memory[label] = k
                else:
                    self.hole_memory[label] = None
    
    @classmethod
    def index_to_label(cls, index:int=None):
        "Integer to string label: 0 -> A1, 1 -> A2, 2 -> A3, 3 -> B1, 4 -> B2, 5 -> B3, 6 -> B4, etc."
        if index is None:
            return None 
        if index not in range(len(cls.strings)):
            raise ValueError(f"index must be in range 1-{len(cls.strings)}: {index=}")
        return cls.strings[index]
    
    @classmethod
    def show_all(cls):
        return IPython.display.SVG(data=cls.svg)
    
    @classmethod
    def show_targets(cls, target_holes:List[str|int|None]=[None]*6):
        """Display implant image with target holes for probes A-F"""
        if len(target_holes) != 6:
            raise ValueError(f"'target_holes' must be a list of 6 integers in range 1-4, or labelled strings (A1, B2, etc.), using None entries as required: {target_holes=}")
        
        if not any(target_holes) and (from_disk := cls.targets_from_disk()):
            targets = from_disk
        else:
            targets = dict()
            # normalize inputs to labelled strings (A1, B2, etc.)
            if all([isinstance(i, int|None) for i in target_holes]):
                for idx, probe in enumerate('ABCDEF'):
                    if hole := target_holes[idx]:
                        targets[probe] = f"{probe}{hole}"
                    else:
                        targets[probe] = None
            elif all([isinstance(i, str|None) for i in target_holes]):
                targets = dict(zip('ABCDEF',target_holes))
        
        for probe, target in targets.items():
            if target and target not in cls.strings:
                target_group = target[0]
                available_labels = cls.labels[target_group]
                raise ValueError(f"Invalid {target=}: available labels are {[f'{target_group}{a}' for a in available_labels]}")
            
        data = cls.svg
        
        for textlabel in cls.strings:
            if textlabel in targets.values(): 
                probe = list(targets.keys())[list(targets.values()).index(textlabel)]
                data = data.replace(f">{textlabel}</tspan>", f"> {probe}</tspan>")
            else:
                data = data.replace(f">{textlabel}</tspan>", f"></tspan>")
        return IPython.display.SVG(data=data)
    
    def set_probe_hole(self, probe:str, hole:None|int|str):
        """Assign a hole to a probe"""
        if probe not in list('ABCDEF'):
            raise ValueError(f"'probe' must be one of A-F: {probe=}")
        if isinstance(hole, int):
            label = self.index_to_label(hole)
        elif hole in [*self.strings, None]:
            label = hole
        elif isinstance(hole,str) and hole.lower() == 'none':
            label = None
        else:
            raise ValueError(f"'hole_index' must be 'A1','B2', etc., or corresponding index, or None: {hole=}")
        
        if self.probe_memory[probe] == label:
            # already assigned
            return
        
        if current_label := self.probe_memory[probe]:
            # probe already assigned to a hole - remove it from the hole_memory
            self.hole_memory[current_label] = None
            
        if label and label in self.probe_memory.values():
            # hole already assigned to other probe(s) - remove previous assignments
            for other_probe in self.probe_memory.keys():
                if self.probe_memory[other_probe] == label:
                    self.set_probe_hole(other_probe,None)
        self.probe_memory[probe] = label
        if label:
            self.hole_memory[label] = probe
    
    def show_memory(self):
        data = self.svg
        for hole, textlabel in self.hole_memory.items():
            if textlabel is None:
                data = data.replace(f">{hole}</tspan>", f"></tspan>")
            else:
                data = data.replace(f">{hole}</tspan>", f"> {textlabel}</tspan>")
        return IPython.display.SVG(data=data) 
    