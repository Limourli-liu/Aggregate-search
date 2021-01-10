from snownlp import SnowNLP

def getSummary(text):
    s=SnowNLP(text)
    return('\n'.join(s.summary(5)))