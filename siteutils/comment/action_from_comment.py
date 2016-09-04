# -*- coding: utf-8 -*-


__author__ = ""
__Copyright__ = "XiaoMaiFeng"


"""
用于小麥蜂网站的评论筛选Library
任意添加需要文件,第三方Libray,可以用C语言作为source code
要求test cases @ test.py

"""

__all__ = ['action_from_comment']


def action_from_comment(comment, platform=None, max_length=256, filter_level=3, *args, **kwargs):
	"""
	用法：传入用户评论，找出用户评论中的关键词，以执行：购买,付款,捐款,其他
		回复方式：Tuple('action', 'extra')
		购买：导出 购买数量: Quantity(默认为1) --> 例如 "I want to buy this" --> ('buy', 1).
		付款：导出 付款金额: Amount(默认为None) 例如 "我要付给小红10块钱" --> ('pay', 10)
		捐款：导出 捐款金额: Amount(默认为None) --> 例如 "wo yao juan kuan" --> ('donate', None)
		其他：其他行为目前全部忽略 --> 例如 "我才不要买" --> ('dajiangyou', None)

	要求：
		1. 轻便快速
		2. 支持简体中文，拼音，繁体中文，英语 (重要性从左到右递减)
		3. 购买物品时用户可以不指出购买数量，默认为1
		4. 捐款或者付款的金额用户可以不指出，若认为没有指出，则默认为None。但是前提一定要是确定用户的行为为付款或者捐款
		5. 若定为其他行为，则视为打酱油
		6. 必须以Tuple形式回复('action', 'extra')
		7. *可以有AI能力，也可以定义Class, 但不要求*

	参数：
		1. comment: String (none coding schema specified), required
		2. platform: String, 表示评论的来源, 例如: 'renren', 'weibo', 'douban'
		3. max_length: Int, 表示最长的filter长度，如果comment超过max_length,则只filter到max_length的长度，返回结果
		4. filter_level: 基于社交网络上的用户评论，大多语句比较简单易懂，所以比如购买，买，買，buy, mai, 都可以作为购买行为，
			但是拼音中mai 和卖谐音，所以可以作为模糊性结果，模糊性结果将被判定为不同的行为取决于参数filter_level.
			filter_level -> 1, 2, 3
			filter_level 1(信任): 模糊性结果将被视为相对应行为 --> 高风险
			filter_level 2(中立): 模糊性结果可以被视为行为或者不视为行为，可以以概率取决(概率可以自己拟定) --> 有风险
			filter_level 3(不信任): 模糊性结果将不被视为相对应行为  --> 低风险
			默认为filter_level 3
			模糊语句可以包括: "不要买我要买" --> 矛盾语句
							"wo yao mai" --> 可以换词的语句
							"买或者不买" --> 疑问性语句
							"你才要付给我呢" --> 收款人付款人颠倒语句
							"买买，我来给你回复个" --> 用户名包括买，mai, 付款，捐款等关键词
							"买你妹" --> 网络流行反话，搞笑用语

			*具体如果可以自己定义，filter_level的每一层level也可以重新定义，模糊性语句也可以重新定义。

		* 如果需要其他参数，请在这里加上:


	"""

	#STUB
	if u'买' in comment:
		return ('buy', 1)
	else:
		return ('dajiangyou', None)








