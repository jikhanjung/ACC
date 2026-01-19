import math
from collections import defaultdict
from itertools import combinations


# ------------------------------------------------------------
# 1. 덴드로그램을 위한 간단한 트리 구조 (예시)
# ------------------------------------------------------------
class DendroNode:
    """
    예시용 덴드로그램 노드.
    members: 이 노드(클러스터)가 포함하는 지역들의 집합
    sim: 이 클러스터가 형성될 때의 유사도 (0~1 가정)
    left/right: 자식 노드 (리프면 None)
    """
    def __init__(self, members, sim, left=None, right=None):
        self.members = set(members)
        self.sim = sim
        self.left = left
        self.right = right


# ------------------------------------------------------------
# 2. 덴드로그램에서 "모든 클러스터" 뽑기
# ------------------------------------------------------------
def extract_clusters_from_dendro(root: DendroNode):
    """
    덴드로그램 전체를 순회하며 (멤버집합, sim_local) 쌍을 모은다.
    리프도 포함한다.
    """
    clusters = []

    def dfs(node):
        if node is None:
            return
        clusters.append({
            "members": set(node.members),
            "sim_local": node.sim,
            # 이하 필드는 나중에 채움
            "sim_global": None,
            "diameter": None,
            "theta": None,
            "center": None,
            "points": {},   # member -> (x,y)
            "midline_angle": 0.0
        })
        dfs(node.left)
        dfs(node.right)

    dfs(root)
    return clusters


# ------------------------------------------------------------
# 3. 포괄(global) 덴드로그램에서 똑같은 멤버셋 찾기
# ------------------------------------------------------------
def find_cluster_in_dendro_by_members(root: DendroNode, target_members: set):
    """
    global 덴드로그램에 똑같은 멤버 구성의 클러스터가 있으면 그 sim을 돌려준다.
    없으면 None
    """
    found = None

    def dfs(node):
        nonlocal found
        if node is None or found is not None:
            return
        if node.members == target_members:
            found = node.sim
            return
        dfs(node.left)
        dfs(node.right)

    dfs(root)
    return found


# ------------------------------------------------------------
# 4. 포괄 유사도 행렬에서 쌍별 평균으로 sim_global 만들기
# ------------------------------------------------------------
def average_pairwise_similarity(members: set, global_matrix: dict):
    """
    members = {"J","T","Y"} 같은 집합
    global_matrix = {("J","T"): 0.8, ("T","J"):0.8, ...} 혹은 중첩 dict
    여기서는 중첩 dict 버전으로 가정:
      global_matrix[a][b] = similarity
    """
    ms = list(members)
    if len(ms) == 1:
        # 한 개만 있으면 자기 자신이니까 1로 잡아도 되고,
        # global에서 못 찾았으면 1로 치자.
        return 1.0

    total = 0.0
    cnt = 0
    for a, b in combinations(ms, 2):
        # 양방향 중 하나만 있다고 가정
        s = None
        if a in global_matrix and b in global_matrix[a]:
            s = global_matrix[a][b]
        elif b in global_matrix and a in global_matrix[b]:
            s = global_matrix[b][a]
        else:
            # 없으면 0으로
            s = 0.0
        total += s
        cnt += 1
    return total / cnt if cnt > 0 else 0.0


# ------------------------------------------------------------
# 5. 각 클러스터에 두 번째 점수(sim_global), 도형 값(d, theta) 붙이기
# ------------------------------------------------------------
def decorate_clusters(clusters, global_dendro: DendroNode, global_matrix: dict, unit=1.0):
    """
    clusters: extract_clusters_from_dendro 로 뽑은 리스트
    global_dendro: 포괄 덴드로그램
    global_matrix: 포괄 유사도 행렬 (중첩 dict)
    unit: 지름 계산할 때 쓸 상수
    """
    for c in clusters:
        members = c["members"]
        # 1) global 덴드로그램에서 찾기
        global_sim = find_cluster_in_dendro_by_members(global_dendro, members)
        if global_sim is None:
            # 2) 없으면 행렬에서 평균
            global_sim = average_pairwise_similarity(members, global_matrix)

        c["sim_global"] = global_sim

        # 지름 d = unit / sim_global  (sim_global=0이면 너무 커지니 보정)
        if global_sim <= 0:
            d = unit * 1000  # 차라리 엄청 크게
        else:
            d = unit / global_sim

        c["diameter"] = d
        c["theta"] = 180.0 * (1.0 - c["sim_local"])  # 서술한 공식


# ------------------------------------------------------------
# 6. 좌표 배치를 위한 유틸
# ------------------------------------------------------------
def pol2cart(r, angle_deg):
    rad = math.radians(angle_deg)
    return (r * math.cos(rad), r * math.sin(rad))


def cart_add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def rotate_point(p, angle_deg):
    rad = math.radians(angle_deg)
    x, y = p
    return (x * math.cos(rad) - y * math.sin(rad),
            x * math.sin(rad) + y * math.cos(rad))


# ------------------------------------------------------------
# 7. 첫 번째(기준) 클러스터 배치
# ------------------------------------------------------------
def place_first_cluster(c):
    """
    c: dict representing cluster
    멤버가 1개면 그냥 원점에
    멤버가 2개 이상이면 theta만큼 벌려서 배치
    """
    center = (0.0, 0.0)
    c["center"] = center
    r = c["diameter"] / 2.0
    theta = c["theta"]

    members = list(c["members"])
    points = {}

    if len(members) == 1:
        points[members[0]] = center
        midline = 0.0
    elif len(members) == 2:
        # -theta/2, +theta/2
        a = pol2cart(r, -theta / 2.0)
        b = pol2cart(r, theta / 2.0)
        points[members[0]] = cart_add(center, a)
        points[members[1]] = cart_add(center, b)
        midline = 0.0
    else:
        # 여러 개면 우선 두 개만 양끝에 두고 나머지는 중간에 골고루
        # 단순화 버전
        step = theta / (len(members) - 1)
        start = -theta / 2.0
        for i, m in enumerate(members):
            ang = start + step * i
            p = pol2cart(r, ang)
            points[m] = cart_add(center, p)
        midline = 0.0

    c["points"] = points
    c["midline_angle"] = midline
    return c


# ------------------------------------------------------------
# 8. 클러스터 안에 점 하나 더 붙이는 케이스
# ------------------------------------------------------------
def add_area_to_cluster(base, new_cluster, global_matrix):
    """
    base: 이미 그려진 클러스터(dict)
    new_cluster: members가 기존 base보다 1개 더 많다고 가정
    global_matrix: 어느 쪽에 붙일지 판단할 때 사용
    """
    base_members = base["members"]
    new_members = new_cluster["members"]

    # 새로 들어온 점
    new_point = list(new_members - base_members)
    if len(new_point) != 1:
        # 1개가 아니면 여기선 처리하지 않고 그대로 리턴
        return base
    new_point = new_point[0]

    # 지름/각도 보정
    final_d = max(base["diameter"], new_cluster["diameter"])
    scale = final_d / base["diameter"]
    # 반지름이 바뀌면 기존 포인트도 스케일
    base_r = final_d / 2.0
    new_points = {}
    for m, (x, y) in base["points"].items():
        # 원점 기준 스케일
        new_points[m] = (x * scale, y * scale)

    # 어느 멤버 쪽에 붙일지 결정: 평균 유사도가 더 큰 쪽
    # 아주 단순하게: base 멤버 중에서 new_point와 유사도가 가장 큰 멤버를 찾는다.
    best_m = None
    best_s = -1.0
    for m in base_members:
        s = 0.0
        if m in global_matrix and new_point in global_matrix[m]:
            s = global_matrix[m][new_point]
        elif new_point in global_matrix and m in global_matrix[new_point]:
            s = global_matrix[new_point][m]
        if s > best_s:
            best_s = s
            best_m = m

    # 그 멤버의 각도를 알아내서 그 방향으로 조금 더 붙이자
    # 각도는 arctan2로 구함
    bx, by = new_points[best_m]
    ang = math.degrees(math.atan2(by, bx))

    # 새 점은 같은 반지름에서 그 각도 쪽
    new_xy = pol2cart(base_r, ang)
    new_points[new_point] = new_xy

    base["points"] = new_points
    base["diameter"] = final_d
    # 각도도 더 작은 쪽으로 통일
    base["theta"] = min(base["theta"], new_cluster["theta"])
    base["members"] = new_members
    # midline은 그대로 0으로 둔다 (간단화)
    base["midline_angle"] = 0.0
    return base


# ------------------------------------------------------------
# 9. 클러스터 둘 합치는 케이스
# ------------------------------------------------------------
def merge_two_clusters(base, new_cluster, global_matrix):
    """
    base: 이미 배치된 클러스터
    new_cluster: 아직 배치 안 된 다른 클러스터
    둘 다 원점 중심으로 돌려서 맞춘 뒤, 가장 비슷한 쌍을 맞대는 방식
    """
    # 우선 새 클러스터도 원점 기준으로 임시 배치
    tmp = place_first_cluster(new_cluster)

    # base + new의 멤버
    merged_members = base["members"] | new_cluster["members"]

    # base 지름/각도와 new 지름/각도 중 큰/작은 것 선택
    final_d = max(base["diameter"], new_cluster["diameter"])
    final_theta = min(base["theta"], new_cluster["theta"])
    base_r = final_d / 2.0

    # base 포인트 스케일
    new_points = {}
    scale_base = final_d / base["diameter"]
    for m, (x, y) in base["points"].items():
        new_points[m] = (x * scale_base, y * scale_base)

    # new 포인트 스케일
    scale_new = final_d / new_cluster["diameter"]
    tmp_points = {}
    for m, (x, y) in tmp["points"].items():
        tmp_points[m] = (x * scale_new, y * scale_new)

    # 어느 점끼리 가장 비슷한지 찾기
    best_pair = None
    best_s = -1.0
    for m1 in base["members"]:
        for m2 in new_cluster["members"]:
            s = 0.0
            if m1 in global_matrix and m2 in global_matrix[m1]:
                s = global_matrix[m1][m2]
            elif m2 in global_matrix and m1 in global_matrix[m2]:
                s = global_matrix[m2][m1]
            if s > best_s:
                best_s = s
                best_pair = (m1, m2)

    # best_pair 기준으로 new 클러스터를 회전시켜서 m2가 m1 방향으로 오게 만든다.
    if best_pair is not None:
        m1, m2 = best_pair
        x1, y1 = new_points[m1]
        target_angle = math.degrees(math.atan2(y1, x1))
        x2, y2 = tmp_points[m2]
        src_angle = math.degrees(math.atan2(x2, y2))  # 잘못된 순서 조심
        # 위 줄은 atan2(y,x)여야 한다
        src_angle = math.degrees(math.atan2(y2, x2))
        rot = target_angle - src_angle
    else:
        rot = 0.0

    for m, (x, y) in tmp_points.items():
        rx, ry = rotate_point((x, y), rot)
        # base 안에 같은 이름 있으면 base 것을 우선
        if m not in new_points:
            new_points[m] = (rx, ry)

    # merge 완료
    base["points"] = new_points
    base["members"] = merged_members
    base["diameter"] = final_d
    base["theta"] = final_theta
    base["midline_angle"] = 0.0
    return base


# ------------------------------------------------------------
# 10. Deep copy utility for cluster snapshots
# ------------------------------------------------------------
def deep_copy_cluster(c):
    """Create a deep copy of cluster dict for step snapshots"""
    return {
        "members": set(c["members"]),
        "sim_local": c["sim_local"],
        "sim_global": c["sim_global"],
        "diameter": c["diameter"],
        "theta": c["theta"],
        "center": tuple(c["center"]) if c["center"] else None,
        "points": dict(c["points"]),
        "midline_angle": c["midline_angle"]
    }


# ------------------------------------------------------------
# 11. 전체 ACC 빌더 (원본 - 단일 병합 버전)
# ------------------------------------------------------------
def build_acc_merged(local_dendro: DendroNode,
                     global_dendro: DendroNode,
                     global_matrix: dict,
                     unit=1.0):
    """
    Build ACC result by merging all clusters into one
    This is the original implementation that returns a single merged result
    """
    # 1) 하위 덴드로그램에서 클러스터 뽑기
    clusters = extract_clusters_from_dendro(local_dendro)

    # 2) 각 클러스터에 sim_global, d, theta 부여
    decorate_clusters(clusters, global_dendro, global_matrix, unit=unit)

    # 3) 유사도 높은 순으로 정렬
    clusters.sort(key=lambda c: c["sim_local"], reverse=True)

    # 4) 첫 클러스터 배치
    base = place_first_cluster(clusters[0])

    # 5) 나머지 클러스터 차례로 붙이기
    for c in clusters[1:]:
        # "base 멤버보다 1개만 많으면" → add_area 케이스라고 간주
        if len(c["members"]) == len(base["members"]) + 1 and base["members"].issubset(c["members"]):
            base = add_area_to_cluster(base, c, global_matrix)
        else:
            base = merge_two_clusters(base, c, global_matrix)

    return base


# ------------------------------------------------------------
# 11. ACC 빌더 - 단계별 버전
# ------------------------------------------------------------
def build_acc_steps(local_dendro: DendroNode,
                   global_dendro: DendroNode,
                   global_matrix: dict,
                   unit=1.0):
    """
    Build ACC step by step and return all intermediate states

    Returns:
        list of dicts, each containing:
        {
            "step": int,
            "action": "initial" | "add_area" | "merge_clusters",
            "current_cluster": dict (deep copy),
            "new_cluster": dict | None,
            "description": str,
            "highlighted_members": set,
        }
    """
    # 1) 하위 덴드로그램에서 클러스터 뽑기
    clusters = extract_clusters_from_dendro(local_dendro)

    # 2) 각 클러스터에 sim_global, d, theta 부여
    decorate_clusters(clusters, global_dendro, global_matrix, unit=unit)

    # 3) 유사도 높은 순으로 정렬
    clusters.sort(key=lambda c: c["sim_local"], reverse=True)

    steps = []

    # 4) 첫 클러스터 배치 - Step 0
    base = place_first_cluster(clusters[0])
    steps.append({
        "step": 0,
        "action": "initial",
        "current_cluster": deep_copy_cluster(base),
        "new_cluster": None,
        "description": f"Initial cluster with {len(base['members'])} members (sim_local={base['sim_local']:.3f})",
        "highlighted_members": set(base["members"])
    })

    # 5) 나머지 클러스터 차례로 붙이기
    for idx, c in enumerate(clusters[1:], start=1):
        prev_members = set(base["members"])

        # "base 멤버보다 1개만 많으면" → add_area 케이스
        if len(c["members"]) == len(base["members"]) + 1 and base["members"].issubset(c["members"]):
            action = "add_area"
            new_members = c["members"] - base["members"]
            base = add_area_to_cluster(base, c, global_matrix)
            description = f"Adding {new_members} to cluster (sim_local={c['sim_local']:.3f})"
        else:
            action = "merge_clusters"
            new_members = c["members"] - base["members"]
            base = merge_two_clusters(base, c, global_matrix)
            description = f"Merging cluster with {len(new_members)} new members (sim_local={c['sim_local']:.3f})"

        # 현재 상태 저장
        steps.append({
            "step": idx,
            "action": action,
            "current_cluster": deep_copy_cluster(base),
            "new_cluster": deep_copy_cluster(c),
            "description": description,
            "highlighted_members": new_members
        })

    return steps


# ------------------------------------------------------------
# 12. 전체 ACC 빌더 (동심원 버전 - 사용하지 않음)
# ------------------------------------------------------------
def build_acc(local_dendro: DendroNode,
              global_dendro: DendroNode,
              global_matrix: dict,
              unit=1.0):
    """
    Build ACC result with multiple concentric circles
    Each cluster gets its own circle based on its diameter

    Returns:
        dict with:
            - 'clusters': list of positioned clusters
            - 'all_members': set of all members across all clusters
    """
    # 1) 하위 덴드로그램에서 클러스터 뽑기
    clusters = extract_clusters_from_dendro(local_dendro)

    # 2) 각 클러스터에 sim_global, d, theta 부여
    decorate_clusters(clusters, global_dendro, global_matrix, unit=unit)

    # 3) 단일 멤버 클러스터 제외 (2개 이상만)
    clusters = [c for c in clusters if len(c["members"]) >= 2]

    # 4) 유사도 높은 순으로 정렬
    clusters.sort(key=lambda c: c["sim_local"], reverse=True)

    # 5) 각 클러스터를 독립적으로 배치
    positioned_clusters = []
    for c in clusters:
        positioned = place_first_cluster(c)
        positioned_clusters.append(positioned)

    # 6) 모든 클러스터와 전체 멤버 반환
    all_members = set()
    for c in positioned_clusters:
        all_members.update(c["members"])

    return {
        "clusters": positioned_clusters,
        "all_members": all_members
    }


# ------------------------------------------------------------
# 12. 사용 예시
# ------------------------------------------------------------
if __name__ == "__main__":
    # 예시용 하위 덴드로그램 (local)
    # (((J,T),Y),(N,(O,Q))) 이런 식이라고 치자
    jt = DendroNode(["J", "T"], sim=0.9)
    jty = DendroNode(["J", "T", "Y"], sim=0.8, left=jt, right=DendroNode(["Y"], sim=1.0))
    oq = DendroNode(["O", "Q"], sim=0.85)
    noq = DendroNode(["N", "O", "Q"], sim=0.75, left=DendroNode(["N"], sim=1.0), right=oq)
    local_root = DendroNode(["J", "T", "Y", "N", "O", "Q"], sim=0.6, left=jty, right=noq)

    # 예시용 포괄 덴드로그램 (global) - 구조가 다를 수 있다
    jt_global = DendroNode(["J", "T"], sim=0.88)
    jy_global = DendroNode(["J", "Y"], sim=0.82)
    jty_global = DendroNode(["J", "T", "Y"], sim=0.78, left=jt_global, right=jy_global)
    oq_global = DendroNode(["O", "Q"], sim=0.83)
    n_global = DendroNode(["N"], sim=1.0)
    noq_global = DendroNode(["N", "O", "Q"], sim=0.7, left=n_global, right=oq_global)
    global_root = DendroNode(["J", "T", "Y", "N", "O", "Q"], sim=0.55, left=jty_global, right=noq_global)

    # 포괄 유사도 행렬 (실제로는 더 빽빽해야 함)
    global_matrix = {
        "J": {"T": 0.88, "Y": 0.82, "N": 0.4, "O": 0.35, "Q": 0.36},
        "T": {"J": 0.88, "Y": 0.80, "N": 0.38, "O": 0.33, "Q": 0.34},
        "Y": {"J": 0.82, "T": 0.80, "N": 0.37, "O": 0.32, "Q": 0.33},
        "N": {"O": 0.7, "Q": 0.68, "J": 0.4},
        "O": {"Q": 0.83, "N": 0.7},
        "Q": {"O": 0.83, "N": 0.68},
    }

    acc_result = build_acc(local_root, global_root, global_matrix, unit=1.0)

    # 결과 출력 (새로운 구조)
    print("ACC all members:", acc_result["all_members"])
    print(f"\nNumber of clusters: {len(acc_result['clusters'])}")
    print("\nCluster details:")
    for idx, cluster in enumerate(acc_result["clusters"], 1):
        print(f"\n  Cluster {idx}:")
        print(f"    Members: {cluster['members']}")
        print(f"    Diameter: {cluster['diameter']:.3f}")
        print(f"    Theta: {cluster['theta']:.2f}°")
        print(f"    Points:")
        for m, p in cluster["points"].items():
            print(f"      {m}: ({p[0]:.3f}, {p[1]:.3f})")
