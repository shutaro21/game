from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.db.models import Sum, Max
from .models import Game, Player, Round, Word
import json, random
import logging

logger = logging.getLogger(__name__)

# インデックス画面
def index(request):
    return render(request, 'linq/index.html', {})

# ゲーム作成処理
def create_game(request):
    if int(request.POST['player_cnt']) % 2 == 1:
        solo_cnt = 1
    elif 'on' in request.POST.getlist('solo'):
        solo_cnt = 2
    else:
        solo_cnt = 0

    game = Game.objects.create(
        player_cnt = request.POST['player_cnt'], 
        start_score = request.POST['start_score'], 
        end_score = request.POST['end_score'], 
        solo_cnt = solo_cnt,
    )
    # エントリー画面に遷移
    return HttpResponseRedirect(reverse('linq:entry', args=(game.id,)))

# エントリー画面
def entry(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    return render(request, 'linq/entry.html', {'game': game, 'player_cnt':range(game.player_cnt)})

# エントリー処理
def entry_player(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    # すでに参加人数が設定人数に達している場合古いエラー
    if game.player_set.count() >= game.player_cnt:
        return render(request, 'linq/error.html', {
            'error_message': "登録人数が上限に達しました。",
        })
    # プレイヤー作成
    player = Player.objects.create(
        game = game, 
        name = request.POST['player_name'], 
        score = game.start_score,
        calc_round = 0,
    )
    # 参加人数が設定人数に達した場合はラウンド１を作成する。
    if game.player_set.count() == game.player_cnt:
        make_round(game_id, 1)
    # メイン画面に遷移する
    return HttpResponseRedirect(reverse('linq:main', args=(player.id, 1)))

# エントリー状況チェエック処理
def check_entry(request, game_id):
    response = {}
    res_players = []
    game = get_object_or_404(Game, pk=game_id)
    current_round = Round.objects.filter(game__id=game_id).aggregate(Max('round_no'))['round_no__max']
    if not current_round:
        current_round = 1
    players = Player.objects.filter(game=game).order_by('id')
    for p in players:
        res_players.append({'id':p.id, 'name':p.name, 'url':reverse('linq:main', args=(p.id, current_round)),})
    response['current_round'] = current_round
    response['players'] = res_players
    return HttpResponse(json.dumps(response))

# メイン画面
def main(request, player_id, round_no):
    player = get_object_or_404(Player, pk=player_id)
    players = Player.objects.filter(game=player.game).order_by('id')
    return render(request, 'linq/main.html', {'player': player, 'round_no':round_no, 'player_cnt':range(player.game.player_cnt) })

# 状況チェック処理
def check(request, player_id, round_no):
    response = {}
    res_players = []
    # 自ラウンドデータを取得
    round = Round.objects.filter(player__id=player_id, round_no=round_no).first()
    # まだなければエントリー中の情報を返す
    if not round:
        player = Player.objects.get(pk=player_id)
        response['status'] = 0
        # ラウンドデータが無いのでプレイヤーデータを取得
        players = Player.objects.filter(game=player.game).order_by('id')
        for p in players:
            res_players.append({'no':'*','name':p.name,'score':p.score,'hint1':'','hint2':''})
        response['players'] = res_players
        return HttpResponse(json.dumps(response))
    # 投票１があればその情報を並び順で返す
    if round.poll11:
        response['poll11'] = round.poll11.order
        response['poll12'] = round.poll12.order
    # 他プレイヤーも含めたラウンドデータを取得
    round_all = Round.objects.filter(game=round.game, round_no=round_no).order_by('order')
    hint1_cnt = 0
    hint2_cnt = 0
    poll11_cnt = 0
    poll21_cnt = 0
    # 返却用プレイヤー情報を作成。ヒント、投票の数を数える。
    for r in round_all:
        if r.poll11:
            if round == r:
                poll1_str = r.poll11.player.name + '－' + r.poll12.player.name
            else:
                poll1_str = '投票済み'
        else:
            poll1_str = '未投票'
        if r.poll21:
            if round == r:
                poll2_str = r.poll21.player.name + '－' + r.poll22.player.name
            else:
                poll2_str = '投票済み'
        else:
            poll2_str = '未投票'
        res_players.append({'no':r.order,'name':r.player.name,'score':r.player.score,'hint1':r.hint1,'hint2':r.hint2,'poll1':poll1_str,'poll2':poll2_str})
        if r.hint1:
            hint1_cnt += 1 
        if r.hint2:
            hint2_cnt += 1 
        if r.poll11:
            poll11_cnt += 1 
        if r.poll21:
            poll21_cnt += 1 
    response['players'] = res_players
    response['word'] = round.word
    # ヒント１の数が自分の順番－１なら「ヒント入力中」
    if hint1_cnt == round.order - 1:
        response['status'] = 1
        response['thinking'] = hint1_cnt + 1
        return HttpResponse(json.dumps(response))
    # そうでなくヒント１の数がプレイヤー数未満なら「ヒント入力待ち」
    if hint1_cnt < round.game.player_cnt:
        response['status'] = 2
        response['thinking'] = hint1_cnt + 1
        return HttpResponse(json.dumps(response))
    # 投票１の数がプレイヤー数未満で
    if poll11_cnt < round.game.player_cnt:
        # 自分の投票１がまだなら「投票中」
        if not round.poll11:
            response['status'] = 3
        # そうでないなら「投票待ち」
        else:
            response['status'] = 4
        return HttpResponse(json.dumps(response))
    # ヒント２の数が自分の順番－１なら「ヒント入力中」
    if hint2_cnt == round.order - 1:
        response['status'] = 1
        response['thinking'] = hint2_cnt + 1
        return HttpResponse(json.dumps(response))
    # そうでなくヒント２の数がプレイヤー数未満なら「ヒント入力待ち」
    if hint2_cnt < round.game.player_cnt:
        response['status'] = 2
        response['thinking'] = hint2_cnt + 1
        return HttpResponse(json.dumps(response))
    # 投票２の数がプレイヤー数未満で
    if poll21_cnt < round.game.player_cnt:
        # 自分の投票２がまだなら「投票中」
        if not round.poll21:
            response['status'] = 3
        # そうでないなら「投票待ち」
        else:
            response['status'] = 4
        return HttpResponse(json.dumps(response))
    # それ以外は「完了」
    response['status'] = 5
    return HttpResponse(json.dumps(response))

# ヒント登録処理
def hint(request, player_id, round_no):
    # ラウンド取得
    round = Round.objects.filter(player__id=player_id, round_no=round_no).first()
    # ヒント１が登録されていなければヒント１に登録
    if not round.hint1:
        round.hint1 = request.GET['hint']
    # そうでなければヒント２に登録
    else:
        round.hint2 = request.GET['hint']
    round.save()
    return HttpResponse(json.dumps({'flg':1}))

# 投票処理
def poll(request, player_id, round_no):
    # 自分のラウンドデータ取得
    round = Round.objects.filter(player__id=player_id, round_no=round_no).first()
    # 投票されたプレイヤーのオブジェクト取得
    player1 = Round.objects.filter(game=round.game, round_no=round_no, order=request.GET['player1']).first()
    player2 = Round.objects.filter(game=round.game, round_no=round_no, order=request.GET['player2']).first()
    # 投票１が登録されたいなければ投票１に登録
    if not round.poll11:
        round.poll11 = player1
        round.poll12 = player2
    # そうでなければ投票２に登録
    else:
        round.poll21 = player1
        round.poll22 = player2
    round.save()
    # 投票２が済んだ人数が設定人数に達した場合は点数計算を行う。
    if Round.objects.filter(game__id=round.game.id, round_no=round_no).exclude(poll21__isnull=True).count() == round.game.player_cnt:
        logger.debug('calc_score:' + str(player_id))
        calc_score(round.game.id, round.round_no)
    return HttpResponse(json.dumps({'flg':1}))

# 結果画面
def result(request, player_id, round_no):
    # 自分のラウンドデータ取得
    round = Round.objects.filter(player__id=player_id, round_no=round_no).first()
    # 全員分のラウンドデータ取得
    round_all = Round.objects.filter(game=round.game, round_no=round_no).order_by('order')
    # 次のラウンド存在確認
    next_round = Round.objects.filter(player__id=player_id, round_no=round_no + 1).first()
    return render(request, 'linq/result.html', {'round': round, 'round_no':round_no, 'round_all':round_all, 'next_round':next_round })

# 点数計算処理
def calc_score(game_id, round_no):
    # 全員分のラウンドデータ取得
    round_all = Round.objects.filter(game__id=game_id, round_no=round_no).order_by('order')
    words = {}
    hit_data =  {}
    # ラウンドIDをキーにしたワード辞書と的中辞書を作成
    for r in round_all:
        words[r.id] = r.word
        hit_data[r.id] = {'poll1_result':0,'poll2_result':0,'self_hit':False,'other_hit':0,'ng_hit':0,'be_other_hit':0,'be_ng_hit':0}
    # ペアプレイヤーをDBに登録
    for r in round_all:
        pair_player = Round.objects.filter(game__id=game_id, round_no=round_no, word=r.word).exclude(player=r.player).exclude(word='？').first()
        # いればペアプレイヤーを設定（無い人もいる）
        if pair_player:
            r.pair_player = pair_player
        r.save()
    # 全員分のラウンドデータ再取得
    round_all = Round.objects.filter(game__id=game_id, round_no=round_no).order_by('order')
    be_hit_words = []
    for r in round_all:
        # 投票先のワードを取得
        word11 = words[r.poll11.id]
        word12 = words[r.poll12.id]
        word21 = words[r.poll21.id]
        word22 = words[r.poll22.id]
        # 投票１があっていて
        if word11 == word12 and not word11 == '？':
            # 自分の分なら自ペア的中フラグを立てる
            if r in [r.poll11, r.poll12]:
                hit_data[r.id]['self_hit'] = True
                hit_data[r.id]['poll1_result'] = 1
            # 自分の分でないなら他ペア的中の数と投票先の被他ペア的中の数をインクリメント。
            else:
                hit_data[r.id]['other_hit'] += 1
                hit_data[r.id]['poll1_result'] = 2
                hit_data[r.poll11.id]['be_other_hit'] += 1
                hit_data[r.poll12.id]['be_other_hit'] += 1
        # 投票２があっていて
        if word21 == word22 and not word21 == '？':
            # 自分の分なら自ペア的中フラグを立てる
            if r in [r.poll21, r.poll22]:
                hit_data[r.id]['self_hit'] = True
                hit_data[r.id]['poll2_result'] = 1
            # 自分の分でないなら他ペア的中の数と投票先の被他ペア的中の数をインクリメント。
            else:
                hit_data[r.id]['other_hit'] += 1
                hit_data[r.id]['poll2_result'] = 2
                hit_data[r.poll21.id]['be_other_hit'] += 1
                hit_data[r.poll22.id]['be_other_hit'] += 1
        # 単独の人に投票していた場合はNG的中の数と投票先の被NG的中の数をインクリメント
        if word11 == '？':
            hit_data[r.id]['ng_hit'] += 1
            hit_data[r.id]['poll1_result'] = 3
            hit_data[r.poll11.id]['be_ng_hit'] += 1
        if word12 == '？':
            hit_data[r.id]['ng_hit'] += 1
            hit_data[r.id]['poll1_result'] = 3
            hit_data[r.poll12.id]['be_ng_hit'] += 1
        if word21 == '？':
            hit_data[r.id]['ng_hit'] += 1
            hit_data[r.id]['poll2_result'] = 3
            hit_data[r.poll21.id]['be_ng_hit'] += 1
        if word22 == '？':
            hit_data[r.id]['ng_hit'] += 1
            hit_data[r.id]['poll2_result'] = 3
            hit_data[r.poll22.id]['be_ng_hit'] += 1
    # 的中辞書データをDBに保存
    for r in round_all:
        r.poll1_result = hit_data[r.id]['poll1_result']
        r.poll2_result = hit_data[r.id]['poll2_result']
        r.self_hit = hit_data[r.id]['self_hit']
        r.other_hit = hit_data[r.id]['other_hit']
        r.ng_hit = hit_data[r.id]['ng_hit']
        r.be_other_hit = hit_data[r.id]['be_other_hit']
        r.be_ng_hit = hit_data[r.id]['be_ng_hit']
        r.save()
    # 全員分のラウンドデータ再取得
    round_all = Round.objects.filter(game__id=game_id, round_no=round_no).order_by('order')
    # 設定した情報をもとに実際の点数計算処理
    for r in round_all:
        r.score = 0
        # 自ペア的中は＋５（相手も的中時のみ）
        if r.self_hit and r.pair_player.self_hit:
            r.score += 5
        # 他ペア的中は＋２
        r.score = r.score + r.other_hit * 2
        # NG的中は－１
        r.score = r.score - r.ng_hit
        # 被他ペア的中は－１
        r.score = r.score - r.be_other_hit
        # 被NG的中は＋１
        r.score = r.score + r.be_ng_hit
        r.save()
        # 重複処理回避
        if r.player.calc_round < round_no:
            # プレイヤーの合計スコア更新
            r.player.score = r.player.score + r.score
            r.player.calc_round = round_no
            r.player.save()
    # プレイヤーの最大スコアが終了スコアに達していなければ次のラウンドデータを作成する。
    if Player.objects.filter(game__id=game_id).aggregate(Max('score'))['score__max'] < Game.objects.get(pk=game_id).end_score:
        make_round(game_id, round_no + 1)

# ラウンド作成処理
def make_round(game_id, round_no):
    # ゲームデータを取得
    game = Game.objects.get(pk=game_id)
    # 順番を決める
    order = list(range(1, game.player_cnt + 1))
    random.shuffle(order)
    # 単語を設定
    # データベースから全単語取得
    word = Word.objects.all()
    word_list = list(word)
    # シャッフルする
    random.shuffle(word_list)
    # プレイヤー数－ソロプレイヤー数を２で割って切り捨てた数の分、player配列に取得する
    word_cnt = (game.player_cnt - game.solo_cnt) // 2
    player_word = []
    for i in range(word_cnt):
        player_word.append(word_list.pop().word)
    # 同じものをペア分として作成する
    player_word = player_word * 2
    # ソロプレイヤー数の分、「？」を追加する
    player_word = player_word + ['？'] * game.solo_cnt
    # シャッフルする
    random.shuffle(player_word)
    # 重複処理回避
    if Round.objects.filter(game = game, round_no = round_no).count() == 0:
        # 各プレイヤーごとにラウンドデータを作成する
        for p in game.player_set.all():
            round = Round.objects.create(
                game = game,
                player = p,
                round_no = round_no,
                order = order.pop(),
                word = player_word.pop(),
            )
