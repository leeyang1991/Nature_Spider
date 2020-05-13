# coding=gbk
from __init__ import *

class Tools:
    '''
    小工具
    '''

    def __init__(self):
        pass

    def mk_dir(self, dir, force=False):

        if not os.path.isdir(dir):
            if force == True:
                os.makedirs(dir)
            else:
                os.mkdir(dir)



class MULTIPROCESS:
    '''
    可对类内的函数进行多进程并行
    由于GIL，多线程无法跑满CPU，对于不占用CPU的计算函数可用多线程
    并行计算加入进度条
    '''

    def __init__(self, func, params):
        self.func = func
        self.params = params
        copy_reg.pickle(types.MethodType, self._pickle_method)
        pass

    def _pickle_method(self, m):
        if m.im_self is None:
            return getattr, (m.im_class, m.im_func.func_name)
        else:
            return getattr, (m.im_self, m.im_func.func_name)

    def run(self, process=-9999, process_or_thread='p', **kwargs):
        '''
        # 并行计算加进度条
        :param func: input a kenel_function
        :param params: para1,para2,para3... = params
        :param process: number of cpu
        :param thread_or_process: multi-thread or multi-process,'p' or 't'
        :param kwargs: tqdm kwargs
        :return:
        '''

        if process > 0:
            if process_or_thread == 'p':
                pool = multiprocessing.Pool(process)
            elif process_or_thread == 't':
                pool = TPool(process)
            else:
                raise IOError('process_or_thread key error, input keyword such as "p" or "t"')

            results = list(tqdm(pool.imap(self.func, self.params), total=len(self.params), **kwargs))
            pool.close()
            pool.join()
            return results
        else:
            if process_or_thread == 'p':
                pool = multiprocessing.Pool()
            elif process_or_thread == 't':
                pool = TPool()
            else:
                raise IOError('process_or_thread key error, input keyword such as "p" or "t"')

            results = list(tqdm(pool.imap(self.func, self.params), total=len(self.params), **kwargs))
            pool.close()
            pool.join()
            return results




class NatureSpider:

    def __init__(self):
        self.__conf__()
        pass

    def __conf__(self):
        '''
        configuration
        '''
        ####### 关键字 #######
        self.keyword = 'global+warming'

        ####### pages #######
        self.page_start = 1
        self.page_end = 300

        ####### threads #######
        self.threads = 20

    def run(self):
        self.get_articles_url()
        self.do_download_fig()

        pass

    def kernel_get_articles_url(self,params):

        attempts = 0
        while 1:
            try:
                url_text_dir,page = params
                product_url = 'https://www.nature.com/search?q={}&page={}'.format(self.keyword, page)
                fname = hashlib.md5(product_url).hexdigest()
                # print product_url
                # print fname
                f = url_text_dir + '{}.txt'.format(fname)
                if os.path.isfile(f):
                    return None
                request = urllib2.Request(product_url)
                response = urllib2.urlopen(request)
                body = response.read()
                fw = open(f, 'w')
                p = re.findall('<a href="/articles/.*? itemprop=', body)
                for i in p:
                    article = i.split('"')[1]
                    url_i = 'https://www.nature.com{}'.format(article)
                    fw.write(url_i + '\n')
                fw.close()
                success = 1
                attempts = 0
            except Exception as e:
                print e
                sleep(10)
                attempts += 1
                success = 0
            if success == 1 or attempts >= 10:
                break
        pass

    def get_articles_url(self):
        url_text_dir = this_root+'urls\\{}\\'.format(self.keyword)
        Tools().mk_dir(url_text_dir,force=True)
        params = []
        for page in range(self.page_start,self.page_end + 1):
            params.append([url_text_dir,page])

        MULTIPROCESS(self.kernel_get_articles_url,params).run(process=20,process_or_thread='t',desc='fetching search pages...')


    def get_article_figs_url(self,url):
        # url = 'https://www.nature.com/articles/s41586-020-2035-0'
        html_dir = this_root+'html\\'
        Tools().mk_dir(html_dir)
        fname = hashlib.md5(url).hexdigest()
        if os.path.isfile(html_dir+fname+'.html'):
            body = open(html_dir+fname+'.html','r').read()
        else:
            request = urllib2.Request(url)
            response = urllib2.urlopen(request)
            body = response.read()
            outf = html_dir + fname + '.html'
            fw = open(outf, 'w')
            fw.write(body)
            fw.close()
        # print body
        # body_f = this_root+'HTML\\new 1.html'
        # body = open(body_f,'r').read()
        metadata_p = re.findall('<script data-test="dataLayer">\n.*?\n</script>',body)
        metadata = metadata_p[0].split('\n')[1]
        metadata = metadata.replace('dataLayer = ','')
        # metadata = metadata.replace(' ','')
        metadata = metadata[:-1]
        null = 'null'
        false = False
        true = True
        dataLayer = eval(metadata)[0]

        article_title = dataLayer['content']['contentInfo']['title']

        png_p = re.findall('media.springernature.com.*?png', body)
        jpg_p = re.findall('media.springernature.com.*?jpg', body)
        png_p = set(png_p)
        jpg_p = set(jpg_p)
        figs_url = []
        for i in png_p:
            fig_i = 'https://{}'.format(i)
            figs_url.append(fig_i)
        for i in jpg_p:
            fig_i = 'https://{}'.format(i)
            figs_url.append(fig_i)
        return article_title,figs_url

        pass

    def do_download_fig(self):
        url_text_dir = this_root + 'urls\\{}\\'.format(self.keyword)
        all_url = []
        for f in os.listdir(url_text_dir):
            fr = open(url_text_dir+f,'r')
            lines = fr.readlines()
            for line in lines:
                line = line.split('\n')[0]
                all_url.append(line)

        MULTIPROCESS(self.kernel_download,all_url).run(process_or_thread='t',process=self.threads)

        pass


    def kernel_download(self,url):
        attempts = 0
        while 1:
            try:
                article_title, figs_url = self.get_article_figs_url(url)
                self.download_fig(article_title, figs_url)
                success = 1
                attempts = 0
            except Exception as e:
                # print e
                # print 'sleep 10 s'
                success = 0
                attempts += 1
                sleep(10)
            if success == 1 or attempts >= 10:
                break
        pass


    def download_fig(self,article_title,figs_url):
        invalid_char = '/\:*"<>|?'
        new_char = ''
        for char in article_title:
            if char in invalid_char:
                new_char += '.'
            else:
                new_char += char
        article_title = new_char
        try:
            save_path = this_root+'jpg\\{}\\{}\\'.format(self.keyword,article_title)
            Tools().mk_dir(save_path,force=True)
        except:
            article_title_new = hashlib.md5(article_title).hexdigest()
            save_path = this_root + 'jpg\\{}\\{}\\'.format(self.keyword, article_title_new)
            Tools().mk_dir(save_path, force=True)
        f_txt = save_path+'article_title.txt'
        fw_txt = open(f_txt,'w')
        fw_txt.write(article_title)
        fw_txt.close()

        for url in figs_url:
            # print url
            try:
                name = url.split('_')[-2]
                suffix = url.split('.')[-1]
                fname = name+'.'+suffix
                if os.path.isfile(save_path + fname):
                    continue
                request = urllib2.Request(url)
                response = urllib2.urlopen(request)
                body = response.read()
                with open(save_path + fname, 'wb') as f:
                    f.write(body)
                pass
            except Exception as e:
                # print e
                pass



def main():
    NatureSpider().run()
    pass


if __name__ == '__main__':
    main()