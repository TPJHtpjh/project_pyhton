from multiprocessing.connection import answer_challenge
from questionRAG import  questions
from question_seek import personal_sum
import random
import re
class access:
    score:str
    responds:list
    def __init__(self,score,responds):
        score=score
        responds=responds
    
def random_question(questions):
    # random8_10=random.randint(0,148)
    # random1_4=random.randint(149,346)
    # random5_7=random.randint(347,655)
    questions1=[a.page_content for a in random.sample(questions[149:347],4)]
    questions2=[b.page_content for b in random.sample(questions[347:656],3)]
    questions3=[c.page_content for c in random.sample(questions[0:149],3)]
    randoms=questions1+questions2+questions3
    
    random_questions=[]
    for questio in randoms:
        ques=re.split(r'题目:|答案:|难度:',re.sub(r'\s','',questio))
        content=ques[1]
        answer=ques[2]
        difficulty=ques[3]
        random_questions.append({'content':content,'answer':answer,'difficulty':difficulty})
    return random_questions


def Judge(ques,respond):
    '''ques为list(question)类，respond为list类'''
    score=0
    responds=[]
    for i,que in ques:
        bool_true=(que.answer=='√'and respond[i] in ['是','对','正确','不错','好','True','true','T','TRUE','Right','right'])
        bool_false=(que.answer=='×'and respond[i] in ['否','错','错误','不对','不正确','False','false','F','Wrong','wrong'])
        bool_=bool_true or bool_false
        if que.answer.lower()==respond[i].lower() or bool_:
            score+=10
        #     ranswer=que.answer
        # else:
        #     ranswer=respond[i]
        responds.append({
            'content':que.content,
            'answer':que.answer,
            'difficulty':que.difficulty,
            'respond':respond[i]
        })
        '''返回access类,score为总分(int),responds为答题情况(dict,key值如上)'''
    return access(score,responds)



if __name__=='__main__':
    
    '''random_question生成10个题目,1-4选择,5-7判断,8-10填空'''
    #r_ten=random_question(questions)
    '''返回格式为字典{
       'contene':str    #题目
       'answer':str     #答案
       'difficulty':str #难度
    }'''
    '''结果测试'''
    #for i in r_ten:
    #   print(i)
    #    print('\n')
    indexs=[]
    for i,q in enumerate(questions):
        que=q.page_content
        if que.find('地球')!=-1:
            indexs.append(i)
            if que.find('专家')!=-1:
                print(f'{i}\n{que[1:]}')
    #print('*'*90)
    #print(indexs)
    '''
    地球：
    [3, 6, 14, 22, 25, 29, 45, 55, 56, 60, 69, 71, 73, 
    106, 123, 142, 150, 159, 161, 163, 179, 180, 204, 
    241, 261, 269, 271, 279, 285, 290, 299, 304, 310, 
    313, 317, 366, 368, 374, 379, 387, 389, 394, 402, 
    418, 419, 435, 437, 457, 470, 472, 481, 483, 486,
    488, 491, 495, 507, 511, 518, 519, 536, 547, 548, 
    550, 551, 552, 557, 560, 573, 580, 590, 591, 595, 
    613, 622, 630, 650]
    3、6、25、56、60、106、填空普通
    45、142、填空专家
    150、179、180、310判断普通
    261、269、285、判断专家
    394、437、488、536选择普通
    435、590、613、622、650选择专家
    '''