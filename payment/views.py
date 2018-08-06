from decimal import Decimal

from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm

from orders.models import Order

from alipay import AliPay
import time,qrcode
import os, sys

# Making sure your key file is adhered to standards.
# you may find examples at tests/certs/ali/ali_private_key.pem
alipay_public_key_string = '''-----BEGIN PUBLIC KEY-----
    MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyXvYW8qHeYFvw9a13w2V/6Y4O87jnOhiv8RWMOl59ztaPVvUCIvkdNHU3259Qu4NqeFcOk532a9VNaBYpriPNwdNs9E6tbLtZzte/nhLiJLn2IS+/6lmuIXSc+ryXPbwgImW+TL9XBWPs97r6kQCwBoZ6gYCnCUc/lhaYrTDNfldE8x05HNw9Lu5cfX7WG9kKI+9cRKl1DFle63YloHzTB0E+RERuwcqhrj0/kFEw0r4mtc534Q6plhO2ZWx0Sbp2tzF+R0aXRTG3lDhwZkoSWhu7H6oYcCJK8krJh9LP1Wlh2TDDDFMpRhu4GPiFLshpyrBNqFON+TX4tJSZFIYLQIDAQAB
-----END PUBLIC KEY-----'''

app_private_key_string = '''-----BEGIN RSA PRIVATE KEY-----
    MIIEpQIBAAKCAQEArCesod1IRgOGTIu+JJtVf41hMw/HmAWcQHgUEJLF0JiF14J1SywT0eDaEyLLekL2Tz/6EpP/fT3N0WKnm+g9oFc5MfAM9jfmMURwjek4u/chiw49/MwriTK+2EiYG3ru7wz+cMd9ZckTIp6QiM3Q1bRurfhs0+AOyik/PwL8nBVZh53e9WNC1kxWdYQI0QSb9T9yzXNUOUcik4txYhISyfkixg0E70gWzalbXMIYbU2PV+E9RaMqN+JHzoPHLiXve9Sb2xzbA86yJ9S1kLhsBZNESR+0geZfWq6IKXGfHat2lKozYpPhkCY/sJOHMJwEDAofE3TOge6eL2Z29h2k5QIDAQABAoIBAQCJphtZPOZZ3N2X/LAm8vCU0UVjn31Wpz29KoXYjpKObDWwEEaauX6LdL7JSCvr8PiieyQHkMBasn0Lq1cayMHln3hC3o5unFl5ESDxxwWu/TWbyuJzbAhvZdzEcJ72cf/zsa8MG+W+6dxb9O7aA76z8NYCUj0p19/bcsl4J3o1jWhvee5Lx26iCOMCAemnhd1mJC7tAx4+uw0vgJ3k+LIbUsh11fuI/QsGsxuHyKPCcza24rIDfwM8vK181pHBa88jNRHXDXnRy4OSz6JcRoX1W7z5wx2jqTT5NkhOTG2s+6DkcxGYA5Z80woT64GU3/XsE6kv0PG8yuxm72IVPCmhAoGBANx7QQI5su4CVlpvOfkZ79KRE0lY0qZsDjrBdjbO9pSb5Ps3KREJPb6NcOGeLYtqe/k5IkOrkKXuJ6LwamK7dDqiFW5AgNqJzpJhMeHkZP98v846HK0kaxbyDf801R3Gq/98axNKpATP965JtqUt4MhZTuWNQX3+ixbjFcAocEHNAoGBAMfjapihzqht+b27NzhUjMNGVaJAR8SpQ6diZNChvb3bMsq8xGBmDf+6hqkR4+WaO2xH8U4PTCVxquvz2oYsCKi0k9+qoIgATvBDh8VJPF5czN0+5Kn91f3tvkjYrsva2TuPkV70HcXbDw6/LaQYmcYo+swS/0NBav9RiLDhGbd5AoGBAMFFhioWPCRphhsGT1Juiw0RQU/VfeqG5D5bIm5PJFYHBkW1B9m4ORjV0fLk/tWshXplvASH22epCbPKfeeInQ1c0d5wysNHc/5bFygGVwai61wzErowJ3PYwa5KONs+Mb3m6dHiZz8UsvBkC6hmPBpEN2YAWj3BKVnpvEJS8HytAoGASoh09ebXvRwM1H9bjsiQGDxAsBhR6nXHAUICH30/1+xFGy2Z9+v16lYt4hsGpFWHNM/6nUW8+fVRa1vpLsB6lhWHUg44f53F0XcMyDaPqQvnY9QQxYYd5ephWp5ZRzAackgNR5+0/lK5YaFNrnNx217qbW/j+LsK35sSYgn9YdkCgYEAh5iNFOD95IDZ2uT5LFpSLszBA7SuJpMicPN+qjfGx122YW3tTpoHQ2UUFV1tMZHZ38QL4lhIFBY2dJSQ3jnyeDv68qD/kPFQyBosuFGiPd5ze4KCvd7PiMoYGoYXlEoxYZU1RYrPITIuO+AUZqpqMT8VXbDWg5X3gJMVmFAbn5g=
-----END RSA PRIVATE KEY-----'''


APP_ID = '2016091900543893'
# NOTIFY_URL = "127.0.0.1:8000/alipay_callback"
NOTIFY_URL = "http://106.12.25.171:8989/alipay_callback"


def init_alipay_cfg():
    '''
    初始化alipay配置
    :return: alipay 对象
    '''
    alipay = AliPay(
        appid=APP_ID,
        app_notify_url=NOTIFY_URL,  # 默认回调url
        app_private_key_string=app_private_key_string,
        alipay_public_key_string=alipay_public_key_string,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug = True  # 默认False ,若开启则使用沙盒环境的支付宝公钥
    )
    return alipay


def get_qr_code(code_url):
    '''
    生成二维码
    :return None
    '''
    #print(code_url)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=1
    )
    qr.add_data(code_url)  # 二维码所含信息
    img = qr.make_image()  # 生成二维码图片
    os.remove(r'./payment/static/img/whh.png')
    img.save(r'./payment/static/img/whh.png')
    print('二维码保存成功！')

def preCreateOrder(subject:'order_desc' , out_trade_no:int, total_amount:(float,'eg:0.01')):
    '''
    创建预付订单
    :return None：表示预付订单创建失败  [或]  code_url：二维码url
    '''
    result = init_alipay_cfg().api_alipay_trade_precreate(
        subject=subject,
        out_trade_no=out_trade_no,
        total_amount=total_amount)
    print('返回值：',result)
    code_url = result.get('qr_code')
    if not code_url:
        print(result.get('预付订单创建失败：','msg'))
        return
    else:
        get_qr_code(code_url)
        #return code_url


def query_order(out_trade_no:int, cancel_time:int and 'secs'):
    '''
    :param out_trade_no: 商户订单号
    :return: None
    '''
    print('预付订单已创建,请在%s秒内扫码支付,过期订单将被取消！'% cancel_time)
    # check order status
    _time = 0
    for i in range(10):
        # check every 3s, and 10 times in all
 
        print("now sleep 2s")
        time.sleep(2)
 
        result = init_alipay_cfg().api_alipay_trade_query(out_trade_no=out_trade_no)
        if result.get("trade_status", "") == "TRADE_SUCCESS":
            print('订单已支付!')
            print('订单查询返回值：',result)
            break
 
        _time += 2
        if _time >= cancel_time:
            cancel_order(out_trade_no,cancel_time)
            return


def cancel_order(out_trade_no:int, cancel_time=None):
    '''
    撤销订单
    :param out_trade_no:
    :param cancel_time: 撤销前的等待时间(若未支付)，撤销后在商家中心-交易下的交易状态显示为"关闭"
    :return:
    '''
    result = init_alipay_cfg().api_alipay_trade_cancel(out_trade_no=out_trade_no)
    #print('取消订单返回值：', result)
    resp_state = result.get('msg')
    action = result.get('action')
    if resp_state=='Success':
        if action=='close':
            if cancel_time:
                print("%s秒内未支付订单，订单已被取消！" % cancel_time)
        elif action=='refund':
            print('该笔交易目前状态为：',action)
 
        return action
 
    else:
        print('请求失败：',resp_state)
        return


def need_refund(out_trade_no:str or int, refund_amount:int or float, out_request_no:str):
    '''
    退款操作
    :param out_trade_no: 商户订单号
    :param refund_amount: 退款金额，小于等于订单金额
    :param out_request_no: 商户自定义参数，用来标识该次退款请求的唯一性,可使用 out_trade_no_退款金额*100 的构造方式
    :return:
    '''
    result = init_alipay_cfg().api_alipay_trade_refund(out_trade_no=out_trade_no,
                                                       refund_amount=refund_amount,
                                                       out_request_no=out_request_no)
 
    if result["code"] == "10000":
        return result  #接口调用成功则返回result
    else:
        return result["msg"] #接口调用失败则返回原因        


def refund_query(out_request_no:str, out_trade_no:str or int):
    '''
    退款查询：同一笔交易可能有多次退款操作（每次退一部分）
    :param out_request_no: 商户自定义的单次退款请求标识符
    :param out_trade_no: 商户订单号
    :return:
    '''
    result = init_alipay_cfg().api_alipay_trade_fastpay_refund_query(out_request_no, out_trade_no=out_trade_no)
 
    if result["code"] == "10000":
        return result  #接口调用成功则返回result
    else:
        return result["msg"] #接口调用失败则返回原因



# def payment_process(request):
#     order_id = request.session.get('order_id')
#     order = get_object_or_404(Order, id=order_id)
#     host = request.get_host()
#     paypal_dict = {
#         'business': settings.PAYPAL_RECEIVER_EMAIL,
#         'amount': '%.2f' % order.get_total_cost().quantize(
#             Decimal('.01')),
#         'item_name': 'Order {}'.format(order.id),
#         'invoice': str(order.id),
#         'currency_code': 'TWD',
#         'notify_url': 'http://{}{}'.format(host,
#                                            reverse('paypal-ipn')),
#         'return_url': 'http://{}{}'.format(host,
#                                            reverse('payment:done')),
#         'cancel_return': 'http://{}{}'.format(host,
#                                               reverse('payment:canceled')),
#     }
#     form = PayPalPaymentsForm(initial=paypal_dict)
#     return render(request,
#                   'payment/process.html',
#                   {'order': order, 'form': form})

def payment_process(request,total_amount):
    cancel_order(1527212120)
    subject = "谢谢惠顾"
    out_trade_no =int(time.time())
    preCreateOrder(subject,out_trade_no,total_amount)
 
    # query_order(out_trade_no,400000)
 
    # print('5s后订单自动退款')
    # time.sleep(5)
    # print(need_refund(out_trade_no,0.01,111))
 
    # print('5s后查询退款')
    # time.sleep(5)
    # print(refund_query(out_request_no=111, out_trade_no=out_trade_no))
    return render(request, 'payment/process.html')


@csrf_exempt
def payment_done(request):
    return render(request, 'payment/done.html')


@csrf_exempt
def payment_canceled(request):
    return render(request, 'payment/canceled.html')
