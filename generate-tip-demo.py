J = {
    "elements": [],
    "connections": [],
}

def unidir_join(a, b):
    global J
    J["connections"].append(
        {"from_node": a, "to_node": b}
    )

def mk_edfa(name, gain, voa=0.0):
    global J
    J["elements"].append(
        {"uid": name, "type": "Edfa", "type_variety": f"fixed{gain}", "operational": {"gain_target": gain, "out_voa": voa}}
    )

def add_att(a, b, att):
    global J
    if att > 0:
        uid = f"att-({a})-({b})"
    else:
        uid = f"splice-({a})-({b})"
    J["elements"].append(
        {"uid": uid, "type": "Fused", "params": {"loss": att}},
    )
    unidir_join(a, uid)
    unidir_join(uid, b)
    return uid


AMS = 'Amsterdam'
BRE = 'Bremen'
COL = 'Cologne'

def build_fiber(city1, city2):
    global J
    J["elements"].append(
        {
            "uid": f"fiber-{city1}-{city2}",
            "type": "Fiber",
            "type_variety": "SSMF",
            "params": {
                "length": 50,
                "length_units": "km",
                "loss_coef": 0.2,
                "con_in": 1.5,
                "con_out": 1.5,
            }
        }
    )

def unidir_patch(a, b):
    global J
    uid = f"patch-({a})-({b})"
    J["elements"].append(
        {
            "uid": uid,
            "type": "Fiber",
            "type_variety": "SSMF",
            "params": {
                "length": 0,
                "length_units": "km",
                "loss_coef": 0.2,
                "con_in": 0.5,
                "con_out": 0.5,
            }
        }
    )
    add_att(a, uid, 0.0)
    add_att(uid, b, 0.0)
    #unidir_join(a, uid)
    #unidir_join(uid, b)

#for CITY in (AMS, BRE,):
for CITY in (AMS, BRE, COL):
    # transceivers
    J["elements"].append(
        {"uid": f"trx-{CITY}", "type": "Transceiver"}
    )
    J["elements"].append(
        {"uid": f"roadm-{CITY}-AD", "type": "Roadm", "params": {"target_pch_out_db": -12.5}}
    )
    unidir_join(f"trx-{CITY}", f"roadm-{CITY}-AD")
    unidir_join(f"roadm-{CITY}-AD", f"trx-{CITY}")

    for n in (1,2):
        J["elements"].append(
            {"uid": f"roadm-{CITY}-L{n}", "type": "Roadm", "params": {"target_pch_out_db": -12.5}}
        )
        mk_edfa(f"roadm-{CITY}-L{n}-booster", 22)
        mk_edfa(f"roadm-{CITY}-L{n}-preamp", 27)
        unidir_join(f"roadm-{CITY}-L{n}", f"roadm-{CITY}-L{n}-booster")
        unidir_join(f"roadm-{CITY}-L{n}-preamp", f"roadm-{CITY}-L{n}")

        unidir_patch(f"roadm-{CITY}-AD", f"roadm-{CITY}-L{n}")
        unidir_patch(f"roadm-{CITY}-L{n}", f"roadm-{CITY}-AD")
        for m in (1,2):
            if m == n:
                continue
            #add_att(f"roadm-{CITY}-L{n}", f"roadm-{CITY}-L{m}", 22)
            unidir_patch(f"roadm-{CITY}-L{n}", f"roadm-{CITY}-L{m}")

#for LONG in ((AMS, BRE), (BRE, AMS)):
#for LONG in ((AMS, BRE),):
#for LONG in ((AMS, BRE), (BRE, COL)):
#for city1, city2 in ((AMS, BRE), (BRE, AMS),):
for city1, city2 in ((AMS, BRE), (BRE, COL), (COL, AMS)):
    build_fiber(city1, city2)
    unidir_join(f"roadm-{city1}-L1-booster", f"fiber-{city1}-{city2}")
    unidir_join(f"fiber-{city1}-{city2}", f"roadm-{city2}-L2-preamp")
    build_fiber(city2, city1)
    unidir_join(f"roadm-{city2}-L2-booster", f"fiber-{city2}-{city1}")
    unidir_join(f"fiber-{city2}-{city1}", f"roadm-{city1}-L1-preamp")


for _, E in enumerate(J["elements"]):
    uid = E["uid"]
    if uid.startswith("roadm-") and (uid.endswith("-L1-booster") or uid.endswith("-L2-booster")):
        E["operational"]["out_voa"] = 12.5
    #if uid.endswith("-AD-add"):
    #    E["operational"]["out_voa"] = 21

import json
print(json.dumps(J, indent=2))
