# arXiv:1303.6254
#
# \sigma(m) = \sigma(m_ref) (m_ref / m)^4 \times (1 + a_1 ((m-m_ref)/m_ref) + a_2 ((m-m_ref)/m_ref)^2)
#
#
#



# TT_Dil              87.315
# TT_Sem              364.352
# TT_Had              380.095
# 87.315
# 364.352
# 380.095


mRef = 172.5

for mass in [169.5, 172.5, 175.5]:
  print('top mass : ' + str(mass) + '\n')
  for xsec in [87.315, 364.352, 380.095]:
    a1 = -0.745
    a2 = 0.127
    sigma= (xsec)*((mRef/mass)**4)*(1+a1*(mass-mRef)/(mRef) + a2*(((mass-mRef)/(mRef))**2) )
    print sigma
  print('------------------')


# 175.5
# 172.5
# 169.5





# top mass : 169.5

# 94.8797909656
# 395.918703521
# 413.025644472
# ------------------
# top mass : 175.5

# 80.4433145755
# 335.677518779
# 350.181545595




# def xsect_vs_mt(  x,  par ):
#     par[0] = m_ref
#     par[1] = sigma(m_ref)
#     par[2] = a_1
#     par[3] = a_2
#     sigma= (par[1])*((par[0]/x[0])**4)*(1+par[2]*(x[0]-par[0])/(par[0]) + par[3]*(((x[0]-par[0])/(par[0]))**2) )
#     return sigma


