import numpy as np
from CoolProp.CoolProp import PropsSI as PSI
from scipy.optimize import minimize
import pandas as pd
from func_fix import (pr_func, pr_deriv, eta_s_PUMP_func, eta_s_PUMP_deriv, turbo_func, turbo_deriv, he_func, he_deriv,
                         ihx_func, ihx_deriv, temperature_func, temperature_deriv, valve_func, valve_deriv,
                         x_saturation_func, x_saturation_deriv, qt_diagram)

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

def hp_simultaneous(target_p32, print_results, plot, case, delta_t_min):

    wf = "REFPROP::R1336MZZZ"
    fluid_TES = "REFPROP::water"
    fluid_ambient = "REFPROP::air"

    # TES
    t21 = 70 + 273.15    # input is known
    p21 = 5e5            # input is known
    t22 = 140 + 273.15   # output temperature is set
    m21 = 10             # dimensioning of the system (full load)

    # PRESSURE DROPS
    pr_cond_cold = 1
    pr_cond_hot = 0.95
    pr_ihx_hot = 0.985
    pr_ihx_cold = 0.985
    pr_eva_cold = 0.95

    pr_cond_part_cold = np.cbrt(pr_cond_cold)  # COND pressure drop is split equally (geom, mean) between ECO-EVA-SH
    pr_cond_part_hot = np.cbrt(pr_cond_hot)    # COND pressure drop is split equally (geom, mean) between ECO-EVA-SH

    # AMBIENT
    t0 = 10 + 273.15   # K
    p0 = 1.013e5      # bar

    # HEAT PUMP
    ttd_l_cond = 5  # K
    ttd_u_ihx = 5   # K
    ttd_l_eva = 5   # K

    # TECHNICAL PARAMETERS
    eta_s = 0.85

    # PRE-CALCULATION
    t32 = t21 + ttd_l_cond
    t34 = t0 - ttd_l_eva
    t36 = t32 - ttd_u_ihx

    # STARTING VALUES
    h31 = 525e3
    h32 = 293e3
    h33 = 233e3
    h34 = 233e3
    h35 = 400e3
    h36 = 450e3
    h38 = 480e3
    h39 = 370e3
    h21 = 293e3
    h22 = 589e3
    h28 = 390e3
    h29 = 540e3

    p31 = 12e5
    p33 = 12.3e5
    p34 = 0.35e5
    p35 = 0.34e5
    p36 = 0.32e5
    p38 = 13e5
    p39 = 13e5
    p22 = 5e5
    p28 = 5e5
    p29 = 5e5

    m31 = 12.8
    power = 1000

    variables = np.array([h36, h31, p31, h32, m31, power, h21, h22, h33, h35, p36, p33, h34, p34, p22, p35,
                          h38, h39, h28, h29, p38, p39, p28, p29])

    residual = np.ones(len(variables))

    iter = 0

    while np.linalg.norm(residual) > 1e-4:
        # TODO [h36, h31, p31, h32, m31, power, h21, h22, h33, h35, p36, p33, h34, p34, p22, p35,
        # TODO   0    1    2    3    4     5     6    7    8    9    10   11   12   13   14   15
        #       h38, h39, h28, h29, p38, p39, p28, p29,])]
        # TODO   16,  17   18   19   20   21   22   23 

        #   0
        eta_s_def = eta_s_PUMP_func(eta_s, variables[0], variables[10], variables[1], variables[2], wf)
        #   1
        t36_set = temperature_func(t36, variables[0], variables[10], wf)
        #   2
        t32_set = temperature_func(t32, variables[3], target_p32, wf)
        #   3
        p31_set = pr_func(pr_cond_hot, variables[2], target_p32)
        #   4
        turbo_en_bal = turbo_func(variables[5], variables[4], variables[0], variables[1])
        #   5
        cond_en_bal = he_func(variables[4], variables[1], variables[3], m21, variables[6], variables[7])
        #   6
        t21_set = temperature_func(t21, variables[6], p21, fluid_TES)
        #   7
        t22_set = temperature_func(t22, variables[7], variables[14], fluid_TES)
        #   8
        ihx_en_bal = ihx_func(variables[3], variables[8], variables[9], variables[0])
        #   9
        p36_set = pr_func(pr_ihx_cold, variables[15], variables[10])
        #   10
        p33_set = pr_func(pr_ihx_hot, target_p32, variables[11])
        #   11
        valve_en_bal = valve_func(variables[8], variables[12])
        #   12
        eva_outlet_sat = x_saturation_func(1, variables[9], variables[15], wf)
        #   13
        t34_set = temperature_func(t34, variables[12], variables[13], wf)
        #   14
        p22_set = pr_func(pr_cond_cold, p21, variables[14])
        #   15
        p35_set = pr_func(pr_eva_cold, variables[13], variables[15])
        #   16
        cond_eco_outlet_sat = x_saturation_func(1, variables[16], variables[20], wf)
        #   17
        cond_eco_en_bal = he_func(variables[4], variables[1], variables[16], m21, variables[19], variables[7])
        #   18
        cond_sh_inlet_sat = x_saturation_func(0, variables[17], variables[21], wf)
        #   19
        cond_sh_en_bal = he_func(variables[4], variables[17], variables[3], m21, variables[6], variables[18])
        # 20
        p38_set = pr_func(pr_cond_part_hot, variables[2], variables[20])
        # 21
        p39_set = pr_func(pr_cond_part_hot, variables[20], variables[21])
        # 22
        p28_set = pr_func(pr_cond_part_cold, p21, variables[22])
        # 23
        p29_set = pr_func(pr_cond_part_cold, variables[22], variables[23])

        residual = np.array([eta_s_def, t36_set, t32_set, p31_set, turbo_en_bal, cond_en_bal, t21_set, t22_set,
                             ihx_en_bal, p36_set, p33_set, valve_en_bal, eva_outlet_sat, t34_set, p22_set, p35_set, 
                             cond_eco_outlet_sat, cond_eco_en_bal, cond_sh_inlet_sat, cond_sh_en_bal, p38_set,
                             p39_set, p28_set, p29_set], dtype=float)
        jacobian = np.zeros((len(variables), len(variables)))

        #   0
        eta_s_def_j = eta_s_PUMP_deriv(eta_s, variables[0], variables[10], variables[1], variables[2], wf)
        #   1
        t36_set_j = temperature_deriv(t36, variables[0], variables[10], wf)
        #   2
        t32_set_j = temperature_deriv(t32, variables[3], target_p32, wf)
        #   3
        p31_set_j = pr_deriv(pr_cond_hot, variables[2], target_p32)
        #   4
        turbo_en_bal_j = turbo_deriv(variables[5], variables[4], variables[0], variables[1])
        #   5
        cond_en_bal_j = he_deriv(variables[4], variables[1], variables[3], m21, variables[6], variables[7])
        #   6
        t21_set_j = temperature_deriv(t21, variables[6], p21, fluid_TES)
        #   7
        t22_set_j = temperature_deriv(t22, variables[7], variables[14], fluid_TES)  # TODO correct p22 with pr_cond_cold
        #   8
        ihx_en_bal_j = ihx_deriv(variables[3], variables[8], variables[9], variables[0])
        #   9
        p36_set_j = pr_deriv(pr_ihx_cold, variables[15], variables[10])
        #   10
        p33_set_j = pr_deriv(pr_ihx_hot, target_p32, variables[11])
        #   11
        valve_en_bal_j = valve_deriv(variables[8], variables[12])
        #   12
        eva_outlet_sat_j = x_saturation_deriv(1, variables[9], variables[15], wf)
        #   13
        t34_set_j = temperature_deriv(t34, variables[12], variables[13], wf)
        #   14
        p22_set_j = pr_deriv(pr_cond_cold, p21, variables[14])
        #   15
        p35_set_j = pr_deriv(pr_eva_cold, variables[13], variables[15])
        #   16
        cond_eco_outlet_sat_j = x_saturation_deriv(1, variables[16], variables[20], wf)
        #   17
        cond_eco_en_bal_j = he_deriv(variables[4], variables[1], variables[16], m21, variables[19], variables[7])
        #   18
        cond_sh_inlet_sat_j = x_saturation_deriv(0, variables[17], variables[21], wf)
        #   19
        cond_sh_en_bal_j = he_deriv(variables[4], variables[17], variables[3], m21, variables[6], variables[18])
        # 20
        p38_set_j = pr_deriv(pr_cond_part_hot, variables[2], variables[20])
        # 21
        p39_set_j = pr_deriv(pr_cond_part_hot, variables[20], variables[21])
        # 22
        p28_set_j = pr_deriv(pr_cond_part_cold, p21, variables[22])
        # 23
        p29_set_j = pr_deriv(pr_cond_part_cold, variables[22], variables[23])

        # TODO [h36, h31, p31, h32, m31, power, h21, h22, h33, h35, p36, p33, h34, p34, p22, p35,
        # TODO   0    1    2    3    4     5     6    7    8    9    10   11   12   13   14   15
        #       h38, h39, h28, h29, p38, p39, p28, p29,])]
        # TODO   16,  17   18   19   20   21   22   23
        jacobian[0, 0] = eta_s_def_j["h_1"]  # derivative of eta_s_def with respect to h36
        jacobian[0, 10] = eta_s_def_j["p_1"]  # derivative of eta_s_def with respect to p36
        jacobian[0, 1] = eta_s_def_j["h_2"]  # derivative of eta_s_def with respect to h31
        jacobian[0, 2] = eta_s_def_j["p_2"]  # derivative of eta_s_def with respect to p31
        jacobian[1, 0] = t36_set_j["h"]  # derivative of t36_set with respect to h36
        jacobian[1, 10] = t36_set_j["p"]  # derivative of t36_set with respect to p36
        jacobian[2, 3] = t32_set_j["h"]  # derivative of t32_set with respect to h32
        jacobian[3, 2] = p31_set_j["p_1"]  # derivative of p31_set with respect to p31
        jacobian[4, 5] = turbo_en_bal_j["P"]  # derivative of turbo_en_bal with respect to power
        jacobian[4, 4] = turbo_en_bal_j["m"]  # derivative of turbo_en_bal with respect to m31
        jacobian[4, 0] = turbo_en_bal_j["h_1"]  # derivative of turbo_en_bal with respect to h36
        jacobian[4, 1] = turbo_en_bal_j["h_2"]  # derivative of turbo_en_bal with respect to h31
        jacobian[5, 1] = cond_en_bal_j["h_1"]  # derivative of cond_en_bal with respect to h31
        jacobian[5, 3] = cond_en_bal_j["h_2"]  # derivative of cond_en_bal with respect to h32
        jacobian[5, 4] = cond_en_bal_j["m_hot"]  # derivative of cond_en_bal with respect to m31
        jacobian[5, 6] = cond_en_bal_j["h_3"]  # derivative of cond_en_bal with respect to h21
        jacobian[5, 7] = cond_en_bal_j["h_4"]  # derivative of cond_en_bal with respect to h22
        jacobian[6, 6] = t21_set_j["h"]  # derivative of t21_set with respect to h21
        jacobian[7, 7] = t22_set_j["h"]  # derivative of t22_set with respect to h22
        jacobian[7, 14] = t22_set_j["p"]  # derivative of t22_set with respect to p22
        jacobian[8, 3] = ihx_en_bal_j["h_1"]  # derivative of ihx_en_bal with respect to h32
        jacobian[8, 8] = ihx_en_bal_j["h_2"]  # derivative of ihx_en_bal with respect to h33
        jacobian[8, 9] = ihx_en_bal_j["h_3"]  # derivative of ihx_en_bal with respect to h35
        jacobian[8, 0] = ihx_en_bal_j["h_4"]  # derivative of ihx_en_bal with respect to h36
        jacobian[9, 10] = p36_set_j["p_2"]  # derivative of p36_set with respect to p36
        jacobian[9, 15] = p36_set_j["p_1"]  # derivative of p36_set with respect to p35
        jacobian[10, 11] = p33_set_j["p_2"]  # derivative of p33_set with respect to p33
        jacobian[11, 12] = valve_en_bal_j["h_2"]  # derivative of valve_en_bal with respect to h34
        jacobian[12, 9] = eva_outlet_sat_j["h"]  # derivative of eva_outlet_sat with respect to h35
        jacobian[12, 15] = eva_outlet_sat_j["p"]  # derivative of eva_outlet_sat with respect to p35
        jacobian[13, 12] = t34_set_j["h"]  # derivative of t34_set with respect to h34
        jacobian[13, 13] = t34_set_j["p"]  # derivative of t34_set with respect to p34
        jacobian[14, 14] = p22_set_j["p_2"]  # derivative of p22_set with respect to p22
        jacobian[15, 13] = p35_set_j["p_1"]  # derivative of p34_set with respect to p34
        jacobian[15, 15] = p35_set_j["p_2"]  # derivative of p34_set with respect to p35
        jacobian[16, 16] = cond_eco_outlet_sat_j["h"]
        jacobian[16, 20] = cond_eco_outlet_sat_j["p"]
        jacobian[17, 4] = cond_eco_en_bal_j["m_hot"]
        jacobian[17, 1] = cond_eco_en_bal_j["h_1"]
        jacobian[17, 16] = cond_eco_en_bal_j["h_2"]
        jacobian[17, 19] = cond_eco_en_bal_j["h_3"]
        jacobian[17, 7] = cond_eco_en_bal_j["h_4"]
        jacobian[18, 17] = cond_sh_inlet_sat_j["h"]
        jacobian[18, 21] = cond_sh_inlet_sat_j["p"]
        jacobian[19, 4] = cond_sh_en_bal_j["m_hot"]
        jacobian[19, 17] = cond_sh_en_bal_j["h_1"]
        jacobian[19, 6] = cond_sh_en_bal_j["h_2"]
        jacobian[19, 3] = cond_sh_en_bal_j["h_3"]
        jacobian[19, 18] = cond_sh_en_bal_j["h_4"]
        jacobian[20, 2] = p38_set_j["p_1"]
        jacobian[20, 20] = p38_set_j["p_2"]
        jacobian[21, 20] = p39_set_j["p_1"]
        jacobian[21, 21] = p39_set_j["p_2"]
        jacobian[22, 22] = p28_set_j["p_2"]
        jacobian[23, 22] = p29_set_j["p_1"]
        jacobian[23, 23] = p29_set_j["p_2"]
        # Convert the numpy array to a pandas DataFrame
        df = pd.DataFrame(jacobian)

        # Save the DataFrame as a CSV file
        df.round(4).to_csv('jacobian_hp.csv', index=False)

        variables -= np.linalg.inv(jacobian).dot(residual)

        iter += 1

        cond_number = np.linalg.cond(jacobian)
        # print("Condition number: ", cond_number, " and residual: ", np.linalg.norm(residual))

    # TODO [h36, h31, p31, h32, m31, power, h21, h22, h33, h35, p36, p33, h34, p34, p22, p35,
    # TODO   0    1    2    3    4     5     6    7    8    9    10   11   12   13   14   15
    #       h38, h39, h28, h29, p38, p39, p28, p29,])]
    # TODO   16,  17   18   19   20   21   22   23

    p31 = variables[2]
    p32 = target_p32
    p33 = variables[11]
    p34 = variables[13]
    p35 = variables[15]
    p36 = variables[10]
    p22 = variables[14]
    p38 = variables[20]
    p39 = variables[21]
    p28 = variables[22]
    p29 = variables[23]

    h31 = variables[1]
    h32 = variables[3]
    h33 = variables[8]
    h34 = variables[12]
    h36 = variables[0]
    h35 = variables[9]
    h21 = variables[6]
    h22 = variables[7]
    h38 = variables[16]
    h39 = variables[17]
    h28 = variables[18]
    h29 = variables[19]

    t31 = PSI("T", "H", h31, "P", p31, wf)
    t32 = PSI("T", "H", h32, "P", p32, wf)
    t33 = PSI("T", "H", h33, "P", p33, wf)
    t34 = PSI("T", "H", h34, "P", p34, wf)
    t35 = PSI("T", "H", h35, "P", p35, wf)
    t36 = PSI("T", "H", h36, "P", p36, wf)
    t21 = PSI("T", "H", h21, "P", p21, fluid_TES)
    t22 = PSI("T", "H", h22, "P", p22, fluid_TES)
    t38 = PSI("T", "H", h38, "P", p38, wf)
    t39 = PSI("T", "H", h39, "P", p39, wf)
    t28 = PSI("T", "H", h28, "P", p28, fluid_TES)
    t29 = PSI("T", "H", h29, "P", p29, fluid_TES)

    s31 = PSI("S", "H", h31, "P", p31, wf)
    s32 = PSI("S", "H", h32, "P", p32, wf)
    s33 = PSI("S", "H", h33, "P", p33, wf)
    s34 = PSI("S", "H", h34, "P", p34, wf)
    s35 = PSI("S", "H", h35, "P", p35, wf)
    s36 = PSI("S", "H", h36, "P", p36, wf)
    s21 = PSI("S", "H", h21, "P", p21, fluid_TES)
    s22 = PSI("S", "H", h22, "P", p22, fluid_TES)
    s38 = PSI("S", "H", h38, "P", p38, wf)
    s39 = PSI("S", "H", h39, "P", p39, wf)
    s28 = PSI("S", "H", h28, "P", p28, fluid_TES)
    s29 = PSI("S", "H", h29, "P", p29, fluid_TES)

    m31 = variables[4]

    df = pd.DataFrame(index=[31, 32, 33, 34, 35, 36, 21, 22, 38, 39, 28, 29],
                      columns=["m [kg/s]", "T [°C]", "h [kJ/kg]", "p [bar]", "s [J/kgK]", "fluid"])
    df.loc[31] = [m31, t31, h31, p31, s31, wf]
    df.loc[32] = [m31, t32, h32, p32, s32, wf]
    df.loc[33] = [m31, t33, h33, p33, s33, wf]
    df.loc[34] = [m31, t34, h34, p34, s34, wf]
    df.loc[35] = [m31, t35, h35, p35, s35, wf]
    df.loc[36] = [m31, t36, h36, p36, s36, wf]
    df.loc[21] = [m21, t21, h21, p21, s21, fluid_TES]
    df.loc[22] = [m21, t22, h22, p21, s22, fluid_TES]
    df.loc[38] = [m31, t38, h38, p38, s38, wf]
    df.loc[39] = [m31, t39, h39, p39, s39, wf]
    df.loc[28] = [m21, t28, h28, p28, s28, fluid_TES]
    df.loc[29] = [m21, t29, h29, p29, s29, fluid_TES]

    df["T [°C]"] = df["T [°C]"] - 273.15
    df["h [kJ/kg]"] = df["h [kJ/kg]"] * 1e-3
    df["p [bar]"] = df["p [bar]"] * 1e-5

    if print_results:
        print("------------------------------------------------------------\n", case, "case")
        print(df.iloc[:, :5])
        print("------------------------------------------------------------")

    P_comp = df.loc[31, "m [kg/s]"] * (df.loc[31, "h [kJ/kg]"] - df.loc[36, "h [kJ/kg]"])
    Q_eva = df.loc[31, "m [kg/s]"] * (df.loc[35, "h [kJ/kg]"] - df.loc[34, "h [kJ/kg]"])
    Q_cond = df.loc[21, "m [kg/s]"] * (df.loc[22, "h [kJ/kg]"] - df.loc[21, "h [kJ/kg]"])

    if round(P_comp+Q_eva-Q_cond) > 1e-5:
        print("Energy balances are not fulfilled! :(")

    '''
    [min_td_cond, max_td_cond] = qt_diagram(df, 'COND', 31, 32, 21, 22, delta_t_min, 'HP',
               plot=plot, case=f'{case}', step_number=300)
    [min_td_cond_sh, max_td_cond_sh] = qt_diagram(df, 'COND-SH', 31, 38, 29, 22, delta_t_min, 'HP',
               plot=plot, case=f'{case}', step_number=300)
    [min_td_cond_eco, max_td_cond_eco] = qt_diagram(df, 'COND-ECO', 39, 32, 21, 28, delta_t_min, 'HP',
               plot=plot, case=f'{case}', step_number=300)
    [min_td_cond_eva, max_td_cond_eva] = qt_diagram(df, 'COND-EVA', 38, 39, 28, 29, delta_t_min, 'HP',
               plot=plot, case=f'{case}', step_number=300)
    qt_diagram(df, 'IHX', 32, 33, 35, 36, delta_t_min, 'HP',
               plot=plot, case=f'{case}', step_number=300)
    '''
    t_pinch_cond_sh = t38-t29

    return df, t_pinch_cond_sh


def epsilon_func(T_0, p_0, df):
    h_0_wf = PSI("H", "T", T_0, "P", p_0, df.loc[31, 'fluid']) * 1e-3
    s_0_wf = PSI("S", "T", T_0, "P", p_0, df.loc[31, 'fluid']) * 1e-3
    e31 = df.loc[31, 'h [kJ/kg]'] - h_0_wf - T_0 * (df.loc[31, 's [J/kgK]'] - s_0_wf) * 1e-3
    e32 = df.loc[32, 'h [kJ/kg]'] - h_0_wf - T_0 * (df.loc[32, 's [J/kgK]'] - s_0_wf) * 1e-3
    e33 = df.loc[33, 'h [kJ/kg]'] - h_0_wf - T_0 * (df.loc[33, 's [J/kgK]'] - s_0_wf) * 1e-3
    e34 = df.loc[34, 'h [kJ/kg]'] - h_0_wf - T_0 * (df.loc[34, 's [J/kgK]'] - s_0_wf) * 1e-3
    e35 = df.loc[35, 'h [kJ/kg]'] - h_0_wf - T_0 * (df.loc[35, 's [J/kgK]'] - s_0_wf) * 1e-3
    e36 = df.loc[36, 'h [kJ/kg]'] - h_0_wf - T_0 * (df.loc[36, 's [J/kgK]'] - s_0_wf) * 1e-3

    h_0_TES = PSI("H", "T", T_0, "P", p_0, df.loc[21, 'fluid']) * 1e-3
    s_0_TES = PSI("S", "T", T_0, "P", p_0, df.loc[21, 'fluid']) * 1e-3
    e21 = df.loc[21, 'h [kJ/kg]'] - h_0_TES - T_0 * (df.loc[21, 's [J/kgK]'] - s_0_TES) * 1e-3
    e22 = df.loc[22, 'h [kJ/kg]'] - h_0_TES - T_0 * (df.loc[22, 's [J/kgK]'] - s_0_TES) * 1e-3

    epsilon_IHX = (e36 - e35) / (e32 - e33)

    epsilon_COND = (df.loc[21, 'm [kg/s]'] * (e22 - e21)) / (df.loc[31, 'm [kg/s]'] * (e31 - e32))

    epsilon_COMP = (e31 - e36) / (df.loc[31, 'h [kJ/kg]'] - df.loc[36, 'h [kJ/kg]'])

    epsilon = {
        'COMP': epsilon_COMP,
        'COND': epsilon_COND,
        'IHX': epsilon_IHX
    }

    return epsilon


# BASE CASE
p32 = 13 * 1e5
[df, min_t_diff_cond] = hp_simultaneous(p32, print_results=True, plot=False, case='base', delta_t_min=5)
round(df, 5).to_csv('hp_simult_strems.csv')

# OPTIMIZE p32

# the following method is very basic but works quickly
target_min_td_cond = 5
tolerance = 0.001  # relative to min temperature difference
learning_rate = 1e4  # relative to p32
diff = abs(min_t_diff_cond - target_min_td_cond)
step = 0

while diff > tolerance:
    # Adjust p32 based on the difference
    adjustment = (target_min_td_cond - min_t_diff_cond) * learning_rate
    # adjustment is the smaller, the smaller the difference target_min_td_cond - min_td_cond
    p32 += adjustment

    [df, min_t_diff_cond] = hp_simultaneous(p32, print_results=False, plot=False, case='base', delta_t_min=5)
    diff = abs(min_t_diff_cond - target_min_td_cond)

    step += 1
    print(f"Optimization in progress: step = {step}, diff = {round(diff,5)}, p32 = {round(p32*1e-5, 5)} bar.")

print(f"Optimization completed successfully in {step} steps!")
print("Optimized p32:", round(p32*1e-5, 5), "bar.")


[df, min_t_diff_cond] = hp_simultaneous(p32, print_results=True, plot=False, case='optimal base', delta_t_min=5)


# the following method doesn't work if the starting value is far away from the optimal value
'''
from scipy.optimize import minimize
target_min_td_cond = 5


def objective_function(p32):
    _, min_td_cond = hp_simultaneous(p32, print_results=False, plot=False, case='base', delta_t_min=5)
    return abs(min_td_cond - target_min_td_cond)


def numerical_gradient(p32, epsilon=1e-6):
    grad = (objective_function(p32 + epsilon) - objective_function(p32 - epsilon)) / (2 * epsilon)
    return grad


# Initial guess for p32
initial_p32 = 12.5 * 1e5

# Using BFGS algorithm for optimization
result = minimize(objective_function, initial_p32, method='BFGS', jac=numerical_gradient)

optimized_p32 = result.x
print("Optimized p32:", optimized_p32)
'''

# EXERGY ANALYSIS
T_0 = 283.15  # K
p_0 = 1.013e5  # Pa
epsilon = epsilon_func(T_0, p_0, df)
df_epsilon = pd.DataFrame.from_dict(epsilon, orient='index', columns=['Value'])
df_epsilon.to_csv('hp_simult_epsilon.csv')




