cellist = [];nil
(LteSimCli.find("/ltesim/rec/cell*1")|LteSimCli.find("/ltesim/rec/cell*2")).attributes.each{|cell|cellist.push(cell[1][0]+cell[1][1]+cell[1][2]+cell[1][3])};nil


antcellist = [];nil
(LteSimCli.find("/ltesim/rec/ant_cell*1")|LteSimCli.find("/ltesim/rec/ant_cell*2")).attributes.each{|elem|antcellist.push(elem[1][3] + elem[1][2])};nil

#cellist.each_index{|i|p cellist[i] + antcellist[i]}

puts "=" * 80;nil
cellist.each do |c|
        antcellist.each do |ant|
                if c[1] == ant[1]
                        c = c + ant[2..3]
                end
        end
        p c
end;nil
puts "=" * 80;nil


