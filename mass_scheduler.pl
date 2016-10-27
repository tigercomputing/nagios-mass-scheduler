#!/usr/bin/perl

###########################################################################################
#   This script provides help to acknowledge multiple services during a large maintenance
#   Sometimes host groups and service groups do not suffice
#      Script reads nrpe.cfg for the location of the status.dat and the FIFO file
#      Script should be able to write to the FIFO file
#      Command is run interactively
#      Santiago Velasco - sanxiago.com
#########################################################################################

$nagios_config = '/etc/nagios3/nagios.cfg';

eval {
    local $SIG{ALRM} = sub { die "timeout" };
    alarm 600;
    $input = main();
    alarm 0;
    exit 0;
};
if ($@ and $@ =~ /timeout/) {
    print "Run time out\n";
    close(STATUS);
    die ;
} elsif ($@) {
    close (STATUS);
    die "Other error: $@\n";
}

sub main {
    my $command_file;
    my $status_file;
    if (-r $nagios_config){
        open (CONFIG, $nagios_config);
        while (<CONFIG>){
            $status_file = ($_=~/status_file=(.*)/)?$1:$status_file;
            $command_file = ($_=~/command_file=(.*)/)?$1:$command_file;
        }
        close(CONFIG);
    }
    else {
        print STDERR "FAILED TO READ NAGIOS CONFIG FILE\n";
        exit 1;
    }
    my $time = time();
    my %state = (1 ,'WARNING', 2,'CRITICAL', 3,'UNKNOWN');
    my $user = $ARGV[0];
    my $msg = $ARGV[1];
    my $search_string = $ARGV[2];



    print STDERR "\n\nACKNOWLEDGE AND SCHEDULE DOWNTIME FOR MULTIPLE SERVICES\n\n";

    while(!defined($user) or $user =~ /\;|\[|\]/  or length($user)<=1){
        print STDERR "Type in yout USER that acknowledges:\n";
        $user = <>;
        $user =~ s/\n//;
    }
    while (!defined($msg) or $msg =~ /\;|\[|\]/ or length($msg)<=1 ){
        print STDERR "Type in the MESSAGE that will be used for all acknowledges:\n";
        $msg = <>;
        $msg =~ s/\n//;
    }
    print STDERR "Type in a string that matches the service_description of the services you want to ack.\n Leave it blank to list all alerts):\n";
    $search_string = <>;
    $search_string =~ s/\n//;
    if(length($search_string)<=1){
        $search_string='.*';
    }

    if (-r $status_file){
        open (STATUS, $status_file);
    }
    else {
        print STDERR "FAILED TO READ NAGIOS STATUS FILE\n";
        exit 1;
    }
    while(<STATUS>){
        if($_ =~ /(service|servicestatus) \{/){
            $is_service = 1;
        }
        if($_ =~ /\}/ and $service_description=~/$search_string/){
            $is_service =0;
            if(defined($current_state) and $current_state and $acknowledged==0 and $scheduled_downtime==0 ){
                # Command Format:
                # [time] ACKNOWLEDGE_SVC_PROBLEM;<host_name>;<service_description>;<sticky>;<notify>;<persistent>;<author>;<comment>
                # [time] SCHEDULE_SVC_DOWNTIME;<host_name>;<service_desription><start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
                undef($ack_true);
                print STDERR "\n---------------------------------------------------------\n";
                print STDERR "Acknowledge $service_description @ $host_name $current_state".$state{$current_state}."?\n$plugin_output\n[y/n/s] (s followed by the number of minutes of scheduled downtime) (Enter to skip)\n";
                $ack_true=<>;
                # if acknowledge yes
                if($ack_true=~/^y/){
                    if (!(-w $command_file)){ print STDERR "FAILED TO OPEN FIFO FILE"; exit 1; }
                    open (CMD, '>>'.$command_file);
                    print CMD "[$time] ACKNOWLEDGE_SVC_PROBLEM;$host_name;$service_description;1;0;0;$user;$msg\n";
                    close (CMD);
                    # if schedule downtime
                }elsif($ack_true=~/^s(.*)/){
                    my $duration = $1;
                    if($duration=~/[^\d]*([0-9]+).*/){
                        #expect duration in minutes convert to seconds
                        $duration=int($1)*60;
                    }else{
                        $duration=3600;
                    }
                    my $end_time = $time + $duration;

                    if (!(-w $command_file)){ print STDERR "FAILED TO OPEN FIFO FILE"; exit 1; }
                    open (CMD, '>>'.$command_file);
                    print CMD "[$time] SCHEDULE_SVC_DOWNTIME;$host_name;$service_description;$time;$end_time;1;0;$duration;$user;$msg\n";
                    close (CMD);
                }
            }
            undef($current_state);
            undef($host_name);
        }
        if($is_service){
            if($_=~/host_name\=(.*)/){
                $host_name=$1;
            }
            if($_=~/service_description\=(.*)/){
                $service_description=$1;
            }
            if($_=~/current_state\=([0-9]*)/){
                $current_state=$1;
            }
            if($_=~/problem_has_been_acknowledged\=([0-9]*)/){
                $acknowledged=$1;
            }
            if($_=~/plugin_output\=(.*)/){
                $plugin_output=$1;
            }
            if($_=~/scheduled_downtime_depth\=([0-9]*)/){
                $scheduled_downtime=$1;
            }
        }
    }
    close(STATUS);
}
