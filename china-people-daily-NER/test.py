# In[1]
import logging
from os import truncate
import torch

from transformers.models.auto.tokenization_auto import AutoTokenizer
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - [%(filename)s:%(lineno)d] - %(message)s',
                    datefmt="%m/%d/%Y %H:%M:%S",
                    level=logging.DEBUG,
                    )

# In[2]
from torch.utils.data.dataset import Dataset

id2label = {0: 'O', 1: 'B-LOC', 2: 'I-LOC', 3: 'B-ORG', 4: 'I-ORG', 5: 'B-PER', 6: 'I-PER'}
label2id = {'O': 0, 'B-LOC': 1, 'I-LOC': 2, 'B-ORG': 3, 'I-ORG': 4, 'B-PER': 5, 'I-PER': 6}

class ChinaPeopleDailyNER(Dataset):
    def __init__(self, tokenizer, filename):
        sents, labels = self.read_data(filename)
        encoding, token_labels = self.tokenize_data(sents, labels, tokenizer)
        
        labels = torch.tensor(token_labels)
        logging.debug(encoding["input_ids"].shape)
        logging.debug(labels.shape)
        
        
    def read_data(self, filename):
        """read and preprocess data file, at char-level

        :param filename: e.g. "data/china-people-daily-ner-corpus/example.dev"
        :return sents: e.g. ["厦门海钓在福建", "中国警察"]
        :return labels: e.g. [
                                [(0, 2, "LOC", "厦门"), (5, 7, "LOC", "福建")]
                                [(0, 2, "LOC", "中国")]  
                            ]
        """
        with open(filename, 'r') as f:
            sents = []; labels = []
            for i, line in enumerate(f.read().split("\n\n")):  # line: "厦 o\n门 o\n ..."
                char_and_tag_s = line.split("\n") # char_and_tags [厦 o, 门 o, ...] 
                sent = ""; tags = [] # EXPECT: sent: "厦门海钓"; tags: [(0, 2, LOC)]

                j = 0; tag = (0, 0, "TYPE")
                while j < len(char_and_tag_s):
                    char, tag = char_and_tag_s[j].split(" ")
                    sent += char 
                    if tag == "O": j += 1; continue 
                    elif tag.startswith("B-"): 
                        # double pointer
                        st = j; ed = j + 1 
                        while ed < len(char_and_tag_s) and char_and_tag_s[ed].split(" ")[1] != "O": 
                            sent += char_and_tag_s[ed].split(" ")[0]
                            ed += 1
                        
                        tags.append((st, ed, tag[2:], sent[st:ed]))
                        j = ed

                sents.append(sent)
                labels.append(tags)
        return sents, labels 
    
    def tokenize_data(self, sents, labels, tokenizer):
        # TODO write doc
        """preprocess data, from char-level to token_level

        :param _type_ sents: _description_
        :param _type_ labels: _description_
        :param _type_ tokenizer: _description_
        :return _type_: _description_
        """
        # TODO maybe return_offsets_mapping can help
        encoding = tokenizer(sents, padding=True, truncation=True, return_tensors="pt")
        token_labels = []
        logging.debug(len(encoding["input_ids"][0]))
        for i, (sent, tags) in enumerate(zip(sents, labels)):
            token_tags = [0] * len(encoding["input_ids"][0])
            for st, ed, tag, tag_in_sent in tags:
                # st 对应的 token index; ed - 1(防止char_to_token == None)对应的 token index
                token_st = encoding.char_to_token(i, st)
                token_ed = encoding.char_to_token(i, ed - 1)
                token_tags[token_st] = label2id[f"B-{tag}"]
                if token_ed > token_st + 1:
                    token_tags[token_st + 1 : token_ed + 1] =  [label2id[f"I-{tag}"]] * (token_ed - token_st)
            token_labels.append(token_tags)
        return encoding, token_labels
         
    def __getitem__(self, idx):
        pass

    def __len__(self):
        pass

tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese")
demo_dataset = ChinaPeopleDailyNER(tokenizer, "data/china-people-daily-ner-corpus/example.demo")
train_dataset = ChinaPeopleDailyNER(tokenizer, "data/china-people-daily-ner-corpus/example.train")
dev_dataset = ChinaPeopleDailyNER(tokenizer, "data/china-people-daily-ner-corpus/example.dev")
test_dataset = ChinaPeopleDailyNER(tokenizer, "data/china-people-daily-ner-corpus/example.test")