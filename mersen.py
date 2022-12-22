

class Randomizer:
    periodN = 624
    periodM = 397

    def __init__(self):
        self.rndIter = 0
        self.rndNumbers = []

    def GenerateState(self):
        mag01 = [0x0, 0x9908B0DF]
        for i in range(Randomizer.periodN - Randomizer.periodM):
            num = int((self.rndNumbers[i] & 0x80000000) | (self.rndNumbers[i + 1] & 0x7FFFFFFF))
            self.rndNumbers[i] = self.rndNumbers[i + Randomizer.periodM] ^ (num >> 1) ^ mag01[num & 0x1]
          # print(Randomizer.rndNumbers[i])
        for i in range(i+1, Randomizer.periodN - 1):
            num = int((self.rndNumbers[i] & 0x80000000) | (self.rndNumbers[i + 1] & 0x7FFFFFFF))
            self.rndNumbers[i] = int(self.rndNumbers[i + (Randomizer.periodM - Randomizer.periodN)] ^ (num >> 1) ^ mag01[num & 0x1])
            # print(Randomizer.rndNumbers[i])
        num = int((self.rndNumbers[Randomizer.periodN - 1] & 0x80000000) | (self.rndNumbers[0] & 0x7FFFFFFF))
        self.rndNumbers[Randomizer.periodN - 1] = int(self.rndNumbers[Randomizer.periodM - 1] ^ (num >> 1) ^ mag01[num & 0x1])
        self.rndIter = 0
       # print(Randomizer.rndNumbers[Randomizer.periodN - 1])

    def Generate(self, seed):
        # Randomizer.rndNumbers[0] = seed
        self.rndNumbers.insert(0, seed)
        i = 1
        for i in range(i, Randomizer.periodN):
            buf = 1812433253 * (self.rndNumbers[i - 1] ^ (self.rndNumbers[i - 1] >> 30)) + i
            buf &= 0xffffffff
            self.rndNumbers.insert(i, buf)
           # print(Randomizer.rndNumbers[i])
        Randomizer.GenerateState(self)

    def Random(self, minimum, maximum):
        if self.rndIter >= Randomizer.periodN:
            Randomizer.GenerateState(self)
        num = self.rndNumbers[self.rndIter]
        self.rndIter += 1
        # print(num)
        num &= 0xFFFFFFFF
        num ^= (num >> 11)
        num ^= (num << 7) & 0x9D2C5680
        num ^= (num << 15) & 0xEFC60000
        num ^= (num >> 18)
        abc = minimum + int(float((num * (1.0 / 4294967296.0)) * float((maximum - minimum + 1))))
        return abc


# a = Randomizer()
# a.Generate(1)
# i = 0
# for i in range(50):
#     b = (a.Random(0x1000, 0xFFFF)|a.Random(0x1000, 0xFFFF))
#     print(b)
# c = Randomizer()
# c.Generate(2)
# i = 0
# for i in range(50):
#     d = (a.Random(0x1000, 0xFFFF)|a.Random(0x1000, 0xFFFF))
#     print(d)
# print(a.rndIter)
