lis = [
    [6.49, -2.41, 71.26, 229, 708, 164],
    [11.54, -1.22, 71.85, 228, 689, 158],
    [17.05, -0.16, 72.64, 229, 664, 172],
    [22.93, 0.57, 73.6, 236, 633, 202],
    [29.03, 0.9, 74.61, 245, 601, 244],
    [35.19, 0.84, 75.54, 258, 569, 294],
    [41.3, 0.44, 76.32, 273, 538, 350],
    [47.26, -0.15, 76.91, 288, 507, 409],
    [52.99, -0.82, 77.33, 303, 466, 468],
    [58.37, -1.48, 77.5, 319, 415, 528],
]

sumOfFirstHalf = [0, 0, 0, 0, 0, 0]
sumOfSecondHalf = [0, 0, 0, 0, 0, 0]

for i in range(len(lis)):
    for j in range(6):
        if (i < 5):
            sumOfFirstHalf[j] += lis[i][j]
        else:
            sumOfSecondHalf[j] += lis[i][j]

diffYPR = abs(sumOfFirstHalf[0] - sumOfSecondHalf[0])
diffYPR += abs(sumOfFirstHalf[1] - sumOfSecondHalf[1])
diffYPR += abs(sumOfFirstHalf[2] - sumOfSecondHalf[2])
diffXYZ = abs(sumOfFirstHalf[3] - sumOfSecondHalf[3])
diffXYZ += abs(sumOfFirstHalf[4] - sumOfSecondHalf[4])
diffXYZ += abs(sumOfFirstHalf[5] - sumOfSecondHalf[5])
print(sumOfFirstHalf)
print(sumOfSecondHalf)
print(diffYPR)
print(diffXYZ)
